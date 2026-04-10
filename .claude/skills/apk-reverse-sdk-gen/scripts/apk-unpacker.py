#!/usr/bin/env python3
"""
APK逆向SDK生成器 - APK解包脚本
使用apktool解包APK获取资源和smali代码
"""

import argparse
import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Optional

def unpack_apk(apk_path: str, output_dir: str, decode_resources: bool = True) -> dict:
    """
    使用apktool解包APK

    Args:
        apk_path: APK文件路径
        output_dir: 输出目录
        decode_resources: 是否解码资源文件

    Returns:
        解包结果信息
    """
    result = {
        "apk_path": apk_path,
        "output_dir": output_dir,
        "success": False,
        "error": None,
        "contents": []
    }

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 构建apktool命令
    cmd = ["apktool", "d", apk_path, "-o", output_dir, "-f"]

    if decode_resources:
        cmd.append("-r")  # 解码资源

    try:
        print(f"执行解包命令: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )

        if process.returncode == 0:
            result["success"] = True

            # 列出解包内容
            output_path = Path(output_dir)
            contents = []

            # 检查主要目录
            main_dirs = ["smali", "smali_classes2", "smali_classes3", "res", "assets", "lib", "original"]
            for d in main_dirs:
                dir_path = output_path / d
                if dir_path.exists():
                    file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
                    contents.append({"directory": d, "file_count": file_count})

            result["contents"] = contents

            print(f"解包成功: {output_dir}")
            print(f"内容统计: {contents}")
        else:
            result["error"] = process.stderr or process.stdout
            print(f"解包失败: {result['error']}")

    except subprocess.TimeoutExpired:
        result["error"] = "解包超时(超过5分钟)"
        print(result["error"])
    except FileNotFoundError:
        result["error"] = "apktool未安装或不在PATH中"
        print(result["error"])
    except Exception as e:
        result["error"] = str(e)
        print(f"解包异常: {e}")

    return result


def extract_apk_info(apk_path: str) -> dict:
    """使用apktool提取APK基本信息"""
    info = {
        "package_name": None,
        "version_name": None,
        "version_code": None,
        "min_sdk": None,
        "target_sdk": None,
        "permissions": [],
        "activities": [],
        "services": [],
        "receivers": [],
    }

    try:
        # 使用apktool dump badging
        result = subprocess.run(
            ["aapt", "dump", "badging", apk_path],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            import re
            for line in result.stdout.split('\n'):
                # 包信息
                if line.startswith('package:'):
                    match = re.search(r"name='([^']+)'", line)
                    if match:
                        info["package_name"] = match.group(1)
                    match = re.search(r"versionName='([^']+)'", line)
                    if match:
                        info["version_name"] = match.group(1)
                    match = re.search(r"versionCode='([^']+)'", line)
                    if match:
                        info["version_code"] = match.group(1)

                # SDK信息
                if line.startswith('sdkVersion:'):
                    info["min_sdk"] = line.split(':')[1].strip()
                if line.startswith('targetSdkVersion:'):
                    info["target_sdk"] = line.split(':')[1].strip()

                # 权限
                if line.startswith('uses-permission:'):
                    match = re.search(r"name='([^']+)'", line)
                    if match:
                        info["permissions"].append(match.group(1))

                # Activity
                if line.startswith('launchable-activity:'):
                    match = re.search(r"name='([^']+)'", line)
                    if match:
                        info["activities"].append(match.group(1))

    except Exception as e:
        print(f"提取APK信息失败: {e}")

    return info


def main():
    parser = argparse.ArgumentParser(description="APK解包工具(apktool)")
    parser.add_argument("--apk", required=True, help="APK文件路径")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--decode-resources", action="store_true", default=True, help="解码资源文件")
    parser.add_argument("--info-only", action="store_true", help="仅提取APK信息不解包")

    args = parser.parse_args()

    # 验证APK文件存在
    if not Path(args.apk).exists():
        print(f"错误: APK文件不存在: {args.apk}")
        sys.exit(1)

    if args.info_only:
        # 仅提取信息
        info = extract_apk_info(args.apk)
        print(json.dumps(info, indent=2, ensure_ascii=False))
        sys.exit(0)

    # 执行解包
    result = unpack_apk(args.apk, args.output, args.decode_resources)

    # 同时提取基本信息
    info = extract_apk_info(args.apk)
    result["apk_info"] = info

    # 保存结果
    output_path = Path(args.output)
    with open(output_path / "unpack-result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()