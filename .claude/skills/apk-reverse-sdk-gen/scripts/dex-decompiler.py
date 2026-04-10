#!/usr/bin/env python3
"""
APK逆向SDK生成器 - DEX反编译脚本
使用jadx反编译DEX文件为Java源码
"""

import argparse
import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Optional, List

def decompile_dex(dex_path: str, output_dir: str, jadx_path: str = "jadx") -> dict:
    """
    使用jadx反编译DEX文件

    Args:
        dex_path: DEX文件或目录路径
        output_dir: 输出目录
        jadx_path: jadx命令路径

    Returns:
        反编译结果信息
    """
    result = {
        "dex_path": dex_path,
        "output_dir": output_dir,
        "success": False,
        "error": None,
        "stats": {}
    }

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 构建jadx命令
    cmd = [
        jadx_path,
        "-d", output_dir,
        "--show-bad-code",  # 显示错误代码
        "--no-debug-info",  # 不生成调试信息
        "--deobf",          # 启用反混淆
        "--deobf-min", "2", # 反混淆最小名称长度
        "--deobf-max", "64",# 反混淆最大名称长度
        "--deobf-use-sourcename",  # 使用源文件名
        "--export-csv",     # 导出CSV格式的信息
        dex_path
    ]

    try:
        print(f"执行反编译命令: {' '.join(cmd)}")
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )

        if process.returncode == 0:
            result["success"] = True

            # 统计反编译结果
            output_path = Path(output_dir)

            # 统计Java文件
            java_files = list(output_path.rglob("*.java"))
            result["stats"]["java_files"] = len(java_files)

            # 统计资源文件
            res_files = list(output_path.rglob("*.xml"))
            result["stats"]["xml_files"] = len(res_files)

            # 检查主目录结构
            sources_dir = output_path / "sources"
            resources_dir = output_path / "resources"

            if sources_dir.exists():
                # 获取包结构
                packages = [d.name for d in sources_dir.iterdir() if d.is_dir()]
                result["stats"]["packages"] = packages

            print(f"反编译成功: {output_dir}")
            print(f"统计: Java文件={result['stats']['java_files']}, XML文件={result['stats']['xml_files']}")
        else:
            result["error"] = process.stderr or process.stdout
            print(f"反编译失败: {result['error']}")

    except subprocess.TimeoutExpired:
        result["error"] = "反编译超时(超过10分钟)"
        print(result["error"])
    except FileNotFoundError:
        result["error"] = "jadx未安装或不在PATH中"
        print(result["error"])
        print("下载地址: https://github.com/skylot/jadx/releases")
    except Exception as e:
        result["error"] = str(e)
        print(f"反编译异常: {e}")

    return result


def decompile_apk(apk_path: str, output_dir: str, jadx_path: str = "jadx") -> dict:
    """直接反编译APK文件"""
    return decompile_dex(apk_path, output_dir, jadx_path)


def main():
    parser = argparse.ArgumentParser(description="DEX反编译工具(jadx)")
    parser.add_argument("--dex", required=True, help="DEX文件或目录路径")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument("--jadx-path", default="jadx", help="jadx命令路径")
    parser.add_argument("--apk", action="store_true", help="输入是APK文件而非DEX目录")

    args = parser.parse_args()

    # 验证输入路径存在
    input_path = Path(args.dex)
    if not input_path.exists():
        print(f"错误: 输入路径不存在: {args.dex}")
        sys.exit(1)

    # 执行反编译
    if args.apk:
        result = decompile_apk(args.dex, args.output, args.jadx_path)
    else:
        result = decompile_dex(args.dex, args.output, args.jadx_path)

    # 保存结果
    output_path = Path(args.output)
    with open(output_path / "decompile-result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()