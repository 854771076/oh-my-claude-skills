#!/usr/bin/env python3
"""
APK Reverse Engineering SDK Generator - Environment Checker
环境检测与安装脚本 V1.0

功能:
- 检测 Java/JDK 版本
- 检测 apktool/jadx/Frida/FART
- 检测 Python 必需包
- 检测 Android 设备连接状态
- 提供自动安装缺失依赖的选项
"""

import subprocess
import sys
import os
import json
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil

# 设置UTF-8编码支持(Windows兼容)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Windows兼容符号
if sys.platform == 'win32':
    SYMBOL_OK = '[OK]'
    SYMBOL_FAIL = '[FAIL]'
    SYMBOL_WARN = '[WARN]'
    SYMBOL_INFO = '  '
else:
    SYMBOL_OK = '✓'
    SYMBOL_FAIL = '✗'
    SYMBOL_WARN = '⚠'
    SYMBOL_INFO = '  '

def print_header(msg: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{msg}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

def print_success(msg: str):
    print(f"{Colors.OKGREEN}{SYMBOL_OK} {msg}{Colors.ENDC}")

def print_warning(msg: str):
    print(f"{Colors.WARNING}{SYMBOL_WARN} {msg}{Colors.ENDC}")

def print_error(msg: str):
    print(f"{Colors.FAIL}{SYMBOL_FAIL} {msg}{Colors.ENDC}")

def print_info(msg: str):
    print(f"{Colors.OKCYAN}{SYMBOL_INFO}{msg}{Colors.ENDC}")

# 必需依赖配置
JAVA_MIN_VERSION = 11

PYTHON_REQUIRED_PACKAGES = [
    ("frida", "16.0.0", "动态调试框架"),
    ("frida-tools", "12.0.0", "Frida工具集"),
    ("pycryptodome", "3.19.0", "加密处理"),
    ("requests", "2.31.0", "HTTP请求"),
    ("lxml", "4.9.0", "XML解析"),
    ("beautifulsoup4", "4.12.0", "HTML解析"),
    ("loguru", "0.7.0", "日志工具"),
]

PYTHON_OPTIONAL_PACKAGES = [
    ("androguard", "3.4.0", "APK分析库"),
    ("apktool-wrapper", "1.0.0", "apktool Python封装"),
    ("jadx-wrapper", "1.0.0", "jadx Python封装"),
]

EXTERNAL_TOOLS = [
    ("java", "Java JDK", ">= 11", "反编译工具基础依赖"),
    ("apktool", "APK解包工具", ">= 2.8", "解包APK获取资源"),
    ("jadx", "DEX反编译工具", ">= 1.4", "反编译DEX为Java源码"),
    ("frida", "动态调试框架", ">= 16", "Hook注入调试"),
    ("frida-server", "Frida服务端", ">= 16", "Android设备端服务"),
]

PACKER_DETECTORS = [
    "360加固", "梆梆加固", "爱加密", "腾讯御安全", "百度加固",
    "阿里聚安全", "网易易盾", "APKProtect", "娜迦加固"
]


class EnvironmentChecker:
    def __init__(self, auto_install: bool = False, silent: bool = False):
        self.auto_install = auto_install
        self.silent = silent
        self.results: Dict[str, Dict] = {}
        self.missing_python: List[str] = []
        self.missing_tools: List[str] = []

    def run_command(self, cmd: List[str], capture: bool = True, shell: bool = False) -> Tuple[bool, str]:
        """执行命令并返回结果"""
        try:
            if sys.platform == 'win32' and not shell:
                executable = shutil.which(cmd[0])
                if executable:
                    cmd = [executable] + cmd[1:]

            if capture:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=shell)
            else:
                result = subprocess.run(cmd, timeout=60, shell=shell)
            return result.returncode == 0, result.stdout if capture else ""
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except FileNotFoundError:
            return False, "Not found"
        except Exception as e:
            return False, str(e)

    def get_java_version(self) -> Optional[int]:
        """获取Java版本"""
        try:
            success, output = self.run_command(["java", "-version"])
            if success and output:
                # 解析版本号 (如: 1.8.0 或 11.0.1)
                import re
                match = re.search(r'version "?(\d+)', output)
                if match:
                    version = int(match.group(1))
                    return version if version >= 9 else version  # 1.x -> x
        except:
            pass
        return None

    def check_tool(self, tool_name: str) -> Tuple[bool, Optional[str]]:
        """检测外部工具是否可用"""
        try:
            if tool_name == "apktool":
                success, output = self.run_command(["apktool", "--version"])
                if success:
                    return True, output.strip().split()[0] if output.strip() else "installed"
            elif tool_name == "jadx":
                success, output = self.run_command(["jadx", "--version"])
                if success:
                    return True, output.strip() if output.strip() else "installed"
            elif tool_name == "frida":
                success, output = self.run_command(["frida", "--version"])
                if success:
                    return True, output.strip()
            elif tool_name == "java":
                version = self.get_java_version()
                if version:
                    return True, str(version)
            elif tool_name == "frida-server":
                # 需要在设备上检测
                return self.check_frida_server()
            else:
                # 通用检测
                executable = shutil.which(tool_name)
                if executable:
                    return True, "installed"
        except:
            pass
        return False, None

    def check_frida_server(self) -> Tuple[bool, Optional[str]]:
        """检测Android设备上的frida-server"""
        try:
            # 检查是否有设备连接
            success, output = self.run_command(["frida-ps", "-U"])
            if success and output:
                return True, "running on device"
        except:
            pass
        return False, None

    def check_android_device(self) -> bool:
        """检测Android设备连接状态"""
        try:
            success, output = self.run_command(["adb", "devices"])
            if success:
                lines = output.strip().split('\n')
                # 检查是否有设备(除了List of devices attached)
                for line in lines[1:]:
                    if line.strip() and 'device' in line:
                        return True
        except:
            pass
        return False

    def check_python_package(self, package: str) -> Tuple[bool, Optional[str]]:
        """检测Python包是否已安装"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
                        return True, version
                return True, "installed"
        except:
            pass
        return False, None

    def check_python_env(self):
        """检测Python环境"""
        if not self.silent:
            print_header("Python Environment Check")

        # Python版本
        py_version = sys.version_info
        version_str = f"{py_version.major}.{py_version.minor}"
        if not self.silent:
            print_success(f"Python version: {version_str}")

        # pip
        success, _ = self.run_command([sys.executable, "-m", "pip", "--version"])
        if success:
            if not self.silent:
                print_success("pip is available")
            self.results["pip"] = {"status": "ok"}
        else:
            if not self.silent:
                print_error("pip is not available")
            self.results["pip"] = {"status": "fail"}

        # 必需包
        if not self.silent:
            print_info("\n必需Python包检测:")
        for package, min_version, desc in PYTHON_REQUIRED_PACKAGES:
            installed, version = self.check_python_package(package)
            if installed:
                if not self.silent:
                    print_success(f"{package} ({desc}) - {version or 'installed'}")
                self.results[f"py_{package}"] = {"status": "ok", "version": version}
            else:
                if not self.silent:
                    print_warning(f"{package} ({desc}) - 未安装")
                self.results[f"py_{package}"] = {"status": "missing"}
                self.missing_python.append(package)

        # 可选包
        if not self.silent:
            print_info("\n可选Python包检测:")
        for package, min_version, desc in PYTHON_OPTIONAL_PACKAGES:
            installed, version = self.check_python_package(package)
            if installed:
                if not self.silent:
                    print_success(f"{package} ({desc}) - {version or 'installed'}")
                self.results[f"py_{package}"] = {"status": "ok", "version": version}
            else:
                if not self.silent:
                    print_info(f"{package} ({desc}) - 未安装 (可选)")
                self.results[f"py_{package}"] = {"status": "missing_optional"}

    def check_external_tools(self):
        """检测外部工具"""
        if not self.silent:
            print_header("External Tools Check")

        for tool_name, display_name, min_version, desc in EXTERNAL_TOOLS:
            installed, version = self.check_tool(tool_name)
            if installed:
                if not self.silent:
                    print_success(f"{display_name} ({desc}) - {version or 'installed'}")
                self.results[f"tool_{tool_name}"] = {"status": "ok", "version": version}
            else:
                if not self.silent:
                    print_warning(f"{display_name} ({desc}) - 未安装")
                self.results[f"tool_{tool_name}"] = {"status": "missing"}
                self.missing_tools.append(tool_name)

    def check_android_env(self):
        """检测Android设备环境"""
        if not self.silent:
            print_header("Android Environment Check")

        if self.check_android_device():
            if not self.silent:
                print_success("Android设备已连接")
            self.results["android_device"] = {"status": "connected"}
        else:
            if not self.silent:
                print_info("未检测到Android设备连接")
            self.results["android_device"] = {"status": "disconnected"}

        frida_server_ok, _ = self.check_frida_server()
        if frida_server_ok:
            if not self.silent:
                print_success("frida-server在设备上运行")
            self.results["frida_server"] = {"status": "running"}
        else:
            if not self.silent:
                print_info("frida-server未在设备上运行")
            self.results["frida_server"] = {"status": "not_running"}

    def install_python_packages(self, packages: List[str]):
        """安装Python包"""
        if not packages:
            return

        print_header("Installing Missing Python Packages")

        skill_dir = Path(__file__).parent.parent
        requirements_file = skill_dir / "requirements.txt"

        if requirements_file.exists():
            print_info(f"使用requirements.txt安装: {requirements_file}")
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            self.run_command(cmd, capture=False)
        else:
            for package in packages:
                print_info(f"安装 {package}...")
                cmd = [sys.executable, "-m", "pip", "install", package]
                self.run_command(cmd, capture=False)

    def generate_report(self) -> Dict:
        """生成环境检测报告"""
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "platform": platform.system(),
            "python": {
                "version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "pip": self.results.get("pip", {}).get("status") == "ok"
            },
            "tools": {tool: self.results.get(f"tool_{tool}", {}).get("status")
                      for _, tool, _, _ in EXTERNAL_TOOLS},
            "android": {
                "device": self.results.get("android_device", {}).get("status"),
                "frida_server": self.results.get("frida_server", {}).get("status")
            },
            "missing_python": self.missing_python,
            "missing_tools": self.missing_tools,
            "all_ok": len(self.missing_python) == 0 and len(self.missing_tools) == 0,
            "details": self.results
        }
        return report

    def save_report(self, output_path: Path):
        """保存报告到文件"""
        report = self.generate_report()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print_info(f"报告已保存: {output_path}")

    def run(self, skill_dir: Path = None, output_file: str = None) -> bool:
        """执行完整的环境检测"""
        if skill_dir is None:
            skill_dir = Path(__file__).parent.parent

        print_header("APK Reverse Engineering SDK Generator - Environment Checker")
        print_info(f"Skill目录: {skill_dir}")
        print_info(f"Python路径: {sys.executable}")

        # 执行检测
        self.check_python_env()
        self.check_external_tools()
        self.check_android_env()

        # 生成总结
        print_header("Environment Check Summary")

        all_ok = True
        critical_missing = []

        if self.missing_python:
            print_warning(f"缺失Python包: {', '.join(self.missing_python)}")
            critical_missing.extend([f"py:{p}" for p in self.missing_python])
            all_ok = False

        if self.missing_tools:
            print_warning(f"缺失外部工具: {', '.join(self.missing_tools)}")
            # Frida-server和Java是可选的
            if 'apktool' in self.missing_tools or 'jadx' in self.missing_tools:
                all_ok = False

        if all_ok:
            print_success("\n[OK] 环境检测通过！核心依赖已就绪。")
        else:
            print_warning("\n[WARN] 环境存在问题，建议安装缺失依赖。")

        # 自动安装
        if critical_missing and self.auto_install:
            print_info("\n开始自动安装缺失Python依赖...")
            self.install_python_packages(self.missing_python)

        # 保存报告
        if output_file:
            self.save_report(skill_dir / output_file)

        return all_ok


def main():
    import argparse

    parser = argparse.ArgumentParser(description="APK逆向环境检测工具")
    parser.add_argument("--auto-install", action="store_true", help="自动安装缺失Python依赖")
    parser.add_argument("--output", type=str, default="environment-report.json", help="输出报告文件名")
    parser.add_argument("--json", action="store_true", help="仅输出JSON报告")
    parser.add_argument("--quiet", action="store_true", help="静默模式")

    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent

    if args.json:
        checker = EnvironmentChecker(auto_install=False, silent=True)
        checker.check_python_env()
        checker.check_external_tools()
        checker.check_android_env()
        report = checker.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["all_ok"] else 1

    if args.quiet:
        checker = EnvironmentChecker(auto_install=args.auto_install, silent=True)
        checker.check_python_env()
        checker.check_external_tools()
        checker.check_android_env()

        if checker.missing_python:
            print(f"MISSING_PYTHON: {','.join(checker.missing_python)}")
        if checker.missing_tools:
            print(f"MISSING_TOOLS: {','.join(checker.missing_tools)}")

        if not checker.missing_python:
            print("ENV_OK")
            return 0
        return 1

    checker = EnvironmentChecker(auto_install=args.auto_install, silent=False)
    all_ok = checker.run(skill_dir, args.output)

    if not all_ok and not args.auto_install:
        print_info("\n提示: 使用 --auto-install 参数自动安装Python依赖")
        print_info("外部工具(apktool/jadx)需手动安装，参考: references/tech-dependencies.md")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())