#!/usr/bin/env python3
"""
APK逆向SDK生成器 - 工作目录初始化脚本
"""

import argparse
import json
import shutil
import sys
import os
from pathlib import Path
from datetime import datetime

def get_apk_info(apk_path: str) -> dict:
    """提取APK基本信息"""
    import subprocess
    import re

    info = {
        "apk_path": apk_path,
        "file_name": Path(apk_path).name,
        "file_size": Path(apk_path).stat().st_size,
        "package_name": None,
        "version": None,
    }

    # 使用aapt或apktool获取包信息
    try:
        # 尝试使用aapt
        result = subprocess.run(
            ["aapt", "dump", "badging", apk_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('package:'):
                    match = re.search(r'name=\'([^\']+)', line)
                    if match:
                        info["package_name"] = match.group(1)
                    match = re.search(r'versionName=\'([^\']+)', line)
                    if match:
                        info["version"] = match.group(1)
                    break
    except:
        pass

    # 如果aapt失败，从文件名推断包名
    if not info["package_name"]:
        # 使用文件名作为包名(去掉.apk后缀)
        info["package_name"] = Path(apk_path).stem.replace('.', '-')

    return info


def create_workspace(apk_path: str, output_dir: str = None, languages: list = None) -> Path:
    """创建工作目录"""

    # 获取APK信息
    apk_info = get_apk_info(apk_path)

    # 确定工作目录
    project_root = Path(output_dir) if output_dir else Path.cwd()
    workspace_name = apk_info["package_name"].replace('.', '_')
    workspace_path = project_root / "apk-projects" / workspace_name

    # 创建目录结构
    dirs = [
        "unpacked",      # APK解包目录
        "decompiled",    # 反编译源码目录
        "unpacked-dex",  # 脱壳后DEX目录
        "analysis",      # 分析结果目录
        "hook-output",   # Hook输出目录
        "output",        # 最终输出目录
        "output/sdk",    # SDK输出目录
        "scripts",       # 脚本目录(复制skill脚本)
        "hooks",         # Hook脚本目录(复制skill hooks)
    ]

    for dir_name in dirs:
        (workspace_path / dir_name).mkdir(parents=True, exist_ok=True)

    # 复制脚本和hooks
    skill_dir = Path(__file__).parent.parent

    # 复制scripts
    scripts_src = skill_dir / "scripts"
    scripts_dst = workspace_path / "scripts"
    if scripts_src.exists():
        for script in scripts_src.glob("*"):
            if script.is_file():
                shutil.copy2(script, scripts_dst / script.name)

    # 复制hooks
    hooks_src = skill_dir / "hooks"
    hooks_dst = workspace_path / "hooks"
    if hooks_src.exists():
        for hook in hooks_src.glob("*"):
            if hook.is_file():
                shutil.copy2(hook, hooks_dst / hook.name)

    # 复制assets
    assets_src = skill_dir / "assets"
    assets_dst = workspace_path / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)

    # 创建配置文件
    config = {
        "apk_info": apk_info,
        "workspace_path": str(workspace_path),
        "created_at": datetime.now().isoformat(),
        "sdk_languages": languages or ["python"],
        "workflow_config": {
            "unpacking": True,
            "decompilation": True,
            "unpacking_detection": True,
            "encryption_analysis": True,
            "api_extraction": True,
            "obfuscation_analysis": True,
            "sdk_generation": True,
        },
        "tools_config": {
            "apktool": {"enabled": True},
            "jadx": {"enabled": True},
            "frida": {"enabled": False},
            "fart": {"enabled": False},
        },
    }

    with open(workspace_path / "project-config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # 创建README
    readme_content = f"""# APK逆向分析项目

## 项目信息

- APK文件: {apk_info['file_name']}
- 包名: {apk_info['package_name']}
- 版本: {apk_info['version'] or 'Unknown'}
- 创建时间: {config['created_at']}
- SDK语言: {', '.join(config['sdk_languages'])}

## 目录结构

```
├── project-config.json    # 项目配置
├── unpacked/              # APK解包目录
├── decompiled/            # 反编译源码
├── unpacked-dex/          # 脱壳后DEX
├── analysis/              # 分析结果
├── hook-output/           # Hook输出
├── output/                # 最终输出
│   ├── sdk/               # SDK代码
│   ├── analysis-report.md # 分析报告
│   └── sdk-document.md    # SDK文档
├── scripts/               # 分析脚本
├── hooks/                 # Frida Hook脚本
└── assets/                # SDK模板
```

## 使用方法

参考 SKILL.md 中的工作流程执行各阶段分析。
"""

    with open(workspace_path / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    return workspace_path


def main():
    parser = argparse.ArgumentParser(description="APK逆向工作目录初始化")
    parser.add_argument("--apk", required=True, help="APK文件路径")
    parser.add_argument("--output", default=None, help="输出目录(默认当前目录)")
    parser.add_argument("--languages", default="python", help="SDK语言(python/java/js，逗号分隔)")

    args = parser.parse_args()

    # 验证APK文件存在
    if not Path(args.apk).exists():
        print(f"错误: APK文件不存在: {args.apk}")
        sys.exit(1)

    # 解析语言列表
    languages = args.languages.split(',') if args.languages else ["python"]

    # 创建工作目录
    workspace_path = create_workspace(args.apk, args.output, languages)

    print(f"工作目录已创建: {workspace_path}")
    print(f"配置文件: {workspace_path / 'project-config.json'}")
    print(f"下一步: cd {workspace_path} 并执行分析脚本")


if __name__ == "__main__":
    main()