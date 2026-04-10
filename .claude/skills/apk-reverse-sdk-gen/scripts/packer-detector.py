#!/usr/bin/env python3
"""
APK逆向SDK生成器 - 加壳检测脚本
检测APK是否使用了加固/加壳技术
"""

import argparse
import json
import sys
import re
import os
from pathlib import Path
from typing import Dict, List, Optional

# 加固厂商特征库
PACKER_SIGNATURES = {
    "360加固": {
        "lib_names": ["libjiagu.so", "libjiagu_64.so", "libjiagu_x86.so"],
        "assets": ["assets/.", "assets/.jiagu"],
        "dex_patterns": ["jiagu"],
        "manifest_meta": ["360加固"],
    },
    "梆梆加固": {
        "lib_names": ["libsecexe.so", "libsecmain.so", "libDexHelper.so"],
        "assets": ["assets/classes.dex", "assets/secexe.jar"],
        "dex_patterns": ["bangbang", "secexe"],
        "manifest_meta": ["bangcl"],
    },
    "爱加密": {
        "lib_names": ["libijiami.so", "libijiami_64.so"],
        "assets": ["assets/ijiami.dat", "assets/ijiami.jar"],
        "dex_patterns": ["ijiami"],
        "manifest_meta": ["ijiami"],
    },
    "腾讯御安全": {
        "lib_names": ["libtosproot.so", "libtosbypass.so"],
        "assets": ["assets/tosproot", "assets/tosbypass"],
        "dex_patterns": ["tos", "tencent"],
        "manifest_meta": ["tencent"],
    },
    "百度加固": {
        "lib_names": ["libbaiduprotect.so"],
        "assets": ["assets/baidu", "assets/baidu.protect"],
        "dex_patterns": ["baidu"],
        "manifest_meta": ["baidu"],
    },
    "阿里聚安全": {
        "lib_names": ["libaliprotect.so", "libsgmain.so"],
        "assets": ["assets/ali", "assets/sgmain"],
        "dex_patterns": ["ali", "sgmain"],
        "manifest_meta": ["ali"],
    },
    "网易易盾": {
        "lib_names": ["libnesec.so", "libnetease.so"],
        "assets": ["assets/netease", "assets/nesec"],
        "dex_patterns": ["netease", "nesec"],
        "manifest_meta": ["netease"],
    },
    "APKProtect": {
        "lib_names": ["libapkprotect.so"],
        "assets": ["assets/apkprotect"],
        "dex_patterns": ["apkprotect"],
        "manifest_meta": ["apkprotect"],
    },
    "娜迦加固": {
        "lib_names": ["libnaga.so", "libnaga_64.so"],
        "assets": ["assets/naga", "assets/naga.dex"],
        "dex_patterns": ["naga"],
        "manifest_meta": ["naga"],
    },
}

# 加壳通用特征
GENERIC_PACKER_INDICATORS = [
    # 资源目录中有隐藏文件
    "assets/.",
    # 多DEX但classes.dex很小
    "small_main_dex",
    # 壳入口特征
    "shell_entry",
    # 原始DEX加密
    "encrypted_dex",
]


def detect_packer_from_files(unpacked_dir: str) -> Dict:
    """从解包文件中检测加壳"""
    result = {
        "detected": False,
        "packer_name": None,
        "confidence": 0,
        "evidence": [],
    }

    unpacked_path = Path(unpacked_dir)
    if not unpacked_path.exists():
        result["error"] = "解包目录不存在"
        return result

    # 检查lib目录
    lib_dir = unpacked_path / "lib"
    if lib_dir.exists():
        for arch_dir in lib_dir.iterdir():
            if arch_dir.is_dir():
                for lib_file in arch_dir.glob("*.so"):
                    lib_name = lib_file.name
                    for packer_name, signatures in PACKER_SIGNATURES.items():
                        if lib_name in signatures.get("lib_names", []):
                            result["detected"] = True
                            result["packer_name"] = packer_name
                            result["confidence"] = 90
                            result["evidence"].append(f"发现壳库: {lib_name} ({arch_dir.name})")

    # 检查assets目录
    assets_dir = unpacked_path / "assets"
    if assets_dir.exists():
        for asset_file in assets_dir.iterdir():
            asset_name = asset_file.name
            for packer_name, signatures in PACKER_SIGNATURES.items():
                # 检查隐藏目录
                for pattern in signatures.get("assets", []):
                    if pattern.startswith("assets/.") and asset_name.startswith("."):
                        result["detected"] = True
                        if not result["packer_name"]:
                            result["packer_name"] = packer_name
                        result["confidence"] = max(result["confidence"], 70)
                        result["evidence"].append(f"发现隐藏assets: {asset_name}")
                    elif asset_name == pattern.split("/")[-1]:
                        result["detected"] = True
                        result["packer_name"] = packer_name
                        result["confidence"] = max(result["confidence"], 85)
                        result["evidence"].append(f"发现壳资源: {asset_name}")

    # 检查smali目录中是否有壳入口
    smali_dir = unpacked_path / "smali"
    if smali_dir.exists():
        for smali_file in smali_dir.rglob("*.smali"):
            content = smali_file.read_text(encoding="utf-8", errors="ignore")
            for packer_name, signatures in PACKER_SIGNATURES.items():
                for pattern in signatures.get("dex_patterns", []):
                    if pattern.lower() in content.lower():
                        result["detected"] = True
                        if not result["packer_name"]:
                            result["packer_name"] = packer_name
                        result["confidence"] = max(result["confidence"], 60)
                        result["evidence"].append(f"发现壳代码特征: {pattern} ({smali_file.name})")

    # 检查DEX大小异常
    original_dir = unpacked_path / "original"
    if original_dir.exists():
        # 壳APK通常在original目录存放原始DEX
        dex_files = list(original_dir.glob("*.dex"))
        if dex_files:
            result["detected"] = True
            result["confidence"] = max(result["confidence"], 80)
            result["evidence"].append(f"发现original目录包含DEX文件")

    return result


def detect_packer_from_decompiled(decompiled_dir: str) -> Dict:
    """从反编译Java代码中检测加壳"""
    result = {
        "detected": False,
        "packer_name": None,
        "confidence": 0,
        "evidence": [],
    }

    decompiled_path = Path(decompiled_dir)
    if not decompiled_path.exists():
        result["error"] = "反编译目录不存在"
        return result

    sources_path = decompiled_path / "sources"
    if not sources_path.exists():
        return result

    # 搜索壳相关类
    for java_file in sources_path.rglob("*.java"):
        try:
            content = java_file.read_text(encoding="utf-8", errors="ignore")

            # 检查壳厂商特征类
            for packer_name, signatures in PACKER_SIGNATURES.items():
                for pattern in signatures.get("dex_patterns", []):
                    if pattern.lower() in content.lower():
                        result["detected"] = True
                        if not result["packer_name"]:
                            result["packer_name"] = packer_name
                        result["confidence"] = max(result["confidence"], 70)
                        result["evidence"].append(f"发现壳类: {java_file.relative_to(sources_path)}")

            # 检查Application壳入口
            if "Application" in content and ("attachBaseContext" in content or "onCreate" in content):
                # 检查是否有动态加载DEX的代码
                if re.search(r'DexFile|PathClassLoader|DexClassLoader|loadClass', content):
                    result["detected"] = True
                    result["confidence"] = max(result["confidence"], 50)
                    result["evidence"].append(f"发现可能的壳Application: {java_file.relative_to(sources_path)}")

        except Exception as e:
            pass

    return result


def detect_packer(apk_path: str, unpacked_dir: str = None, decompiled_dir: str = None) -> Dict:
    """综合检测APK是否加壳"""
    result = {
        "apk_path": apk_path,
        "detected": False,
        "packer_name": None,
        "confidence": 0,
        "evidence": [],
        "recommendation": None,
    }

    # 从解包目录检测
    if unpacked_dir and Path(unpacked_dir).exists():
        file_result = detect_packer_from_files(unpacked_dir)
        if file_result.get("detected"):
            result["detected"] = True
            result["evidence"].extend(file_result.get("evidence", []))
            result["confidence"] = max(result["confidence"], file_result.get("confidence", 0))
            if file_result.get("packer_name") and not result["packer_name"]:
                result["packer_name"] = file_result["packer_name"]

    # 从反编译代码检测
    if decompiled_dir and Path(decompiled_dir).exists():
        code_result = detect_packer_from_decompiled(decompiled_dir)
        if code_result.get("detected"):
            result["detected"] = True
            result["evidence"].extend(code_result.get("evidence", []))
            result["confidence"] = max(result["confidence"], code_result.get("confidence", 0))
            if code_result.get("packer_name") and not result["packer_name"]:
                result["packer_name"] = code_result["packer_name"]

    # 生成建议
    if result["detected"]:
        result["recommendation"] = f"检测到{result['packer_name'] or '未知壳'},建议使用FART进行脱壳处理"
    else:
        result["recommendation"] = "未检测到加壳,可直接进行逆向分析"

    return result


def main():
    parser = argparse.ArgumentParser(description="APK加壳检测工具")
    parser.add_argument("--apk", required=True, help="APK文件路径")
    parser.add_argument("--unpacked", default=None, help="解包目录路径")
    parser.add_argument("--decompiled", default=None, help="反编译目录路径")
    parser.add_argument("--output", default="packer-detection.json", help="输出文件路径")

    args = parser.parse_args()

    # 执行检测
    result = detect_packer(args.apk, args.unpacked, args.decompiled)

    # 输出结果
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 保存结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {args.output}")

    sys.exit(0 if not result.get("detected") else 1)


if __name__ == "__main__":
    main()