#!/usr/bin/env python3
"""
URL Analyzer SDK Generator - Environment Checker
环境检测与安装脚本 V1.0

功能:
- 检测 Python 版本和必需包
- 检测 Node.js 版本和必需包
- 检测浏览器环境
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
PYTHON_MIN_VERSION = (3, 8)
NODE_MIN_VERSION = (16, 0)

PYTHON_REQUIRED_PACKAGES = [
    # 核心依赖
    ("requests", "2.31.0", "基础HTTP请求"),
    ("DrissionPage", "4.0.0", "自动化框架(推荐)"),
    ("lxml", "4.9.0", "XPath解析"),
    ("beautifulsoup4", "4.12.0", "HTML解析"),
    ("pycryptodome", "3.19.0", "加密处理"),
    ("pyexecjs2", "1.0.0", "JS执行"),
    ("loguru", "0.7.0", "日志工具"),
]

PYTHON_OPTIONAL_PACKAGES = [
    ("playwright", "1.40.0", "自动化框架(Playwright抓包需要)"),
    ("curl_cffi", "0.5.10", "TLS指纹模拟"),
    ("ddddocr", "1.4.7", "验证码识别"),
    ("selenium", "4.15.0", "备选自动化"),
    ("scrapy", "2.11.0", "爬虫框架"),
]

NODE_REQUIRED_PACKAGES = [
    # Node.js包全部可选，仅Playwright抓包需要
]

NODE_OPTIONAL_PACKAGES = [
    ("playwright", "1.40.0", "自动化框架(Playwright抓包需要)"),
    ("crypto-js", "4.2.0", "加密库"),
    ("jsdom", "23.0.0", "DOM模拟"),
    ("axios", "1.6.0", "HTTP客户端"),
]

BROWSERS = {
    "chrome": {
        "windows": [
            # 使用注册表或PATH查找
            "chrome.exe",
            # 常见安装路径
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            # 用户目录安装
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
        ],
        "darwin": ["Google Chrome", "/Applications/Google Chrome.app"],
        "linux": ["google-chrome", "google-chrome-stable", "/usr/bin/google-chrome"]
    },
    "edge": {
        "windows": [
            "msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
        ],
        "darwin": ["Microsoft Edge", "/Applications/Microsoft Edge.app"],
        "linux": ["microsoft-edge", "/usr/bin/microsoft-edge"]
    },
    "chromium": {
        "windows": [
            "chromium.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Chromium\Application\chromium.exe"),
        ],
        "darwin": ["Chromium", "/Applications/Chromium.app"],
        "linux": ["chromium", "chromium-browser", "/usr/bin/chromium"]
    },
    "firefox": {
        "windows": [
            "firefox.exe",
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            os.path.expandvars(r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\Mozilla Firefox\firefox.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe"),
        ],
        "darwin": ["Firefox", "/Applications/Firefox.app"],
        "linux": ["firefox", "/usr/bin/firefox"]
    }
}


class EnvironmentChecker:
    def __init__(self, auto_install: bool = False, silent: bool = False):
        self.auto_install = auto_install
        self.silent = silent  # 静默模式，不输出任何彩色信息
        self.results: Dict[str, Dict] = {}
        self.missing_python: List[str] = []
        self.missing_node: List[str] = []
        self.available_browsers: List[str] = []

    def run_command(self, cmd: List[str], capture: bool = True, shell: bool = False) -> Tuple[bool, str]:
        """执行命令并返回结果"""
        try:
            # Windows下需要找到命令的完整路径
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

    def get_python_version(self) -> Optional[Tuple[int, int]]:
        """获取Python版本"""
        try:
            version = sys.version_info
            return (version.major, version.minor)
        except:
            return None

    def get_node_version(self) -> Optional[Tuple[int, int]]:
        """获取Node.js版本"""
        try:
            success, output = self.run_command(["node", "--version"])
            if success and output:
                # v16.0.0 -> (16, 0)
                parts = output.strip().replace("v", "").split(".")
                return (int(parts[0]), int(parts[1]))
        except:
            pass
        return None

    def get_npm_version(self) -> Optional[str]:
        """获取npm版本"""
        try:
            # Windows下npm是npm.cmd批处理脚本
            npm_cmd = "npm"
            if sys.platform == 'win32':
                # 优先使用npm.cmd
                npm_path = shutil.which("npm.cmd")
                if npm_path:
                    npm_cmd = npm_path
                else:
                    npm_path = shutil.which("npm")
                    if npm_path:
                        npm_cmd = npm_path

            success, output = self.run_command([npm_cmd, "--version"])
            if success:
                return output.strip()
        except:
            pass
        return None

    def check_python_package(self, package: str) -> Tuple[bool, Optional[str]]:
        """检测Python包是否已安装 - 使用pip show"""
        try:
            # 使用 pip show 检测包是否安装
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # 提取版本号
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
                        return True, version
                return True, "installed"
        except:
            pass
        return False, None

    def check_node_package(self, package: str, skill_dir: Path) -> Tuple[bool, Optional[str]]:
        """检测Node.js包是否已安装"""
        try:
            # 检查全局和本地安装
            result = subprocess.run(
                ["npm", "list", package, "--depth=0"],
                capture_output=True, text=True, timeout=15,
                cwd=skill_dir if skill_dir.exists() else None
            )
            if result.returncode == 0 and package in result.stdout:
                # 提取版本号
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if package in line and "@" in line:
                        version = line.split("@")[-1].strip()
                        return True, version
            # 检查全局安装
            result = subprocess.run(
                ["npm", "list", "-g", package, "--depth=0"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and package in result.stdout:
                return True, "global"
        except:
            pass
        return False, None

    def check_browser_registry(self, browser_name: str) -> Optional[str]:
        """通过Windows注册表检测浏览器路径"""
        if sys.platform != 'win32':
            return None

        registry_paths = {
            "chrome": [
                (r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", ""),
                (r"SOFTWARE\Google\Update\Clients\{8A69D345-D564-463c-AFF1-A69D9E530F96}", "pv"),
            ],
            "edge": [
                (r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe", ""),
            ],
            "firefox": [
                (r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe", ""),
            ],
        }

        if browser_name not in registry_paths:
            return None

        import winreg
        for reg_path, value_name in registry_paths[browser_name]:
            for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(root, reg_path, 0, winreg.KEY_READ)
                    if value_name:
                        value, _ = winreg.QueryValueEx(key, value_name)
                        # 版本号，尝试构建路径
                        if browser_name == "chrome":
                            possible_paths = [
                                f"C:\\Program Files\\Google\\Chrome\\Application\\{value}\\chrome.exe",
                                os.path.expandvars(f"%LOCALAPPDATA%\\Google\\Chrome\\Application\\{value}\\chrome.exe"),
                            ]
                            for p in possible_paths:
                                if os.path.exists(p):
                                    return p
                    else:
                        # 直接是路径
                        path, _ = winreg.QueryValueEx(key, "")
                        if path and os.path.exists(path):
                            return path
                    winreg.CloseKey(key)
                except:
                    pass
        return None

    def check_browser(self, browser_name: str) -> bool:
        """检测浏览器是否可用"""
        system = platform.system().lower()
        browser_info = BROWSERS.get(browser_name, {})
        paths = browser_info.get(system, [])

        for path in paths:
            if os.path.isabs(path):
                if os.path.exists(path):
                    return True
            else:
                # 尝试在PATH中查找
                if shutil.which(path):
                    return True

        # Windows下额外检查注册表
        if system == 'windows':
            reg_path = self.check_browser_registry(browser_name)
            if reg_path:
                return True

        return False

    def check_python_env(self):
        """检测Python环境"""
        if not self.silent:
            print_header("Python Environment Check")

        # Python版本
        py_version = self.get_python_version()
        if py_version:
            version_str = f"{py_version[0]}.{py_version[1]}"
            if py_version >= PYTHON_MIN_VERSION:
                if not self.silent:
                    print_success(f"Python version: {version_str} (>= {PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]})")
                self.results["python_version"] = {"status": "ok", "version": version_str}
            else:
                if not self.silent:
                    print_error(f"Python version: {version_str} (需要 >= {PYTHON_MIN_VERSION[0]}.{PYTHON_MIN_VERSION[1]})")
                self.results["python_version"] = {"status": "fail", "version": version_str}
        else:
            if not self.silent:
                print_error("Cannot detect Python version")
            self.results["python_version"] = {"status": "unknown"}

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

    def check_node_env(self, skill_dir: Path):
        """检测Node.js环境"""
        if not self.silent:
            print_header("Node.js Environment Check")

        # Node.js版本
        node_version = self.get_node_version()
        if node_version:
            version_str = f"{node_version[0]}.{node_version[1]}"
            if node_version >= NODE_MIN_VERSION:
                if not self.silent:
                    print_success(f"Node.js version: {version_str} (>= {NODE_MIN_VERSION[0]}.{NODE_MIN_VERSION[1]})")
                self.results["node_version"] = {"status": "ok", "version": version_str}
            else:
                if not self.silent:
                    print_error(f"Node.js version: {version_str} (需要 >= {NODE_MIN_VERSION[0]}.{NODE_MIN_VERSION[1]})")
                self.results["node_version"] = {"status": "fail", "version": version_str}
        else:
            if not self.silent:
                print_warning("Node.js未安装 (Playwright抓包需要)")
            self.results["node_version"] = {"status": "missing"}
            return

        # npm
        npm_version = self.get_npm_version()
        if npm_version:
            if not self.silent:
                print_success(f"npm version: {npm_version}")
            self.results["npm"] = {"status": "ok", "version": npm_version}
        else:
            if not self.silent:
                print_error("npm未安装")
            self.results["npm"] = {"status": "fail"}

        # 必需包
        if not self.silent:
            print_info("\n必需Node.js包检测:")
        for package, min_version, desc in NODE_REQUIRED_PACKAGES:
            installed, version = self.check_node_package(package, skill_dir)
            if installed:
                if not self.silent:
                    print_success(f"{package} ({desc}) - {version}")
                self.results[f"node_{package}"] = {"status": "ok", "version": version}
            else:
                if not self.silent:
                    print_warning(f"{package} ({desc}) - 未安装")
                self.results[f"node_{package}"] = {"status": "missing"}
                self.missing_node.append(package)

        # 可选包
        if not self.silent:
            print_info("\n可选Node.js包检测:")
        for package, min_version, desc in NODE_OPTIONAL_PACKAGES:
            installed, version = self.check_node_package(package, skill_dir)
            if installed:
                if not self.silent:
                    print_success(f"{package} ({desc}) - {version}")
                self.results[f"node_{package}"] = {"status": "ok", "version": version}
            else:
                if not self.silent:
                    print_info(f"{package} ({desc}) - 未安装 (可选)")
                self.results[f"node_{package}"] = {"status": "missing_optional"}

    def check_browsers(self):
        """检测浏览器环境"""
        if not self.silent:
            print_header("Browser Environment Check")

        for browser_name in BROWSERS:
            if self.check_browser(browser_name):
                if not self.silent:
                    print_success(f"{browser_name.capitalize()} 可用")
                self.results[f"browser_{browser_name}"] = {"status": "ok"}
                self.available_browsers.append(browser_name)
            else:
                if not self.silent:
                    print_info(f"{browser_name.capitalize()} 未检测到")
                self.results[f"browser_{browser_name}"] = {"status": "missing"}

        if not self.silent:
            if not self.available_browsers:
                print_warning("未检测到任何浏览器，自动化功能可能无法使用")
            else:
                print_success(f"\n可用浏览器: {', '.join(self.available_browsers)}")

    def install_python_packages(self, packages: List[str]):
        """安装Python包"""
        if not packages:
            return

        print_header("Installing Missing Python Packages")

        # 找到requirements.txt
        skill_dir = Path(__file__).parent.parent
        requirements_file = skill_dir / "requirements.txt"

        if requirements_file.exists():
            print_info(f"使用requirements.txt安装: {requirements_file}")
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            success, _ = self.run_command(cmd, capture=False)
            if success:
                print_success("Python依赖安装完成")
            else:
                print_error("Python依赖安装失败，请手动执行:")
                print_info(f"  pip install -r {requirements_file}")
        else:
            # 逐个安装
            for package in packages:
                print_info(f"安装 {package}...")
                cmd = [sys.executable, "-m", "pip", "install", package]
                success, _ = self.run_command(cmd, capture=False)
                if success:
                    print_success(f"{package} 安装成功")
                else:
                    print_error(f"{package} 安装失败")

    def install_node_packages(self, skill_dir: Path):
        """安装Node.js包"""
        if not self.missing_node:
            return

        print_header("Installing Missing Node.js Packages")

        package_json = skill_dir / "package.json"

        if package_json.exists():
            print_info(f"使用package.json安装: {skill_dir}")
            cmd = ["npm", "install"]
            success, _ = self.run_command(cmd, capture=False)
            if success:
                print_success("Node.js依赖安装完成")
            else:
                print_error("Node.js依赖安装失败，请手动执行:")
                print_info(f"  cd {skill_dir} && npm install")
        else:
            # 逐个安装
            for package in self.missing_node:
                print_info(f"安装 {package}...")
                cmd = ["npm", "install", package]
                success, _ = self.run_command(cmd, capture=False)
                if success:
                    print_success(f"{package} 安装成功")
                else:
                    print_error(f"{package} 安装失败")

    def install_playwright_browsers(self):
        """安装Playwright浏览器"""
        print_info("\n安装Playwright浏览器...")
        cmd = [sys.executable, "-m", "playwright", "install"]
        success, _ = self.run_command(cmd, capture=False)
        if success:
            print_success("Playwright浏览器安装完成")
        else:
            print_warning("Playwright浏览器安装失败，请手动执行:")
            print_info("  playwright install")

    def generate_report(self) -> Dict:
        """生成环境检测报告"""
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "platform": platform.system(),
            "python": {
                "version": self.results.get("python_version", {}).get("version"),
                "pip": self.results.get("pip", {}).get("status") == "ok"
            },
            "node": {
                "version": self.results.get("node_version", {}).get("version"),
                "npm": self.results.get("npm", {}).get("version")
            },
            "browsers": self.available_browsers,
            "missing_python": self.missing_python,
            "missing_node": self.missing_node,
            "all_ok": len(self.missing_python) == 0 and len(self.missing_node) == 0,
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

        print_header("URL Analyzer SDK Generator - Environment Checker")
        print_info(f"Skill目录: {skill_dir}")
        print_info(f"Python路径: {sys.executable}")

        # 执行检测
        self.check_python_env()
        self.check_node_env(skill_dir)
        self.check_browsers()

        # 生成总结
        print_header("Environment Check Summary")

        all_ok = True
        critical_missing = []

        # Python必需包检查
        if self.missing_python:
            print_warning(f"缺失Python必需包: {', '.join(self.missing_python)}")
            critical_missing.extend([f"py:{p}" for p in self.missing_python])
            all_ok = False

        # Node.js检查 (Playwright抓包需要)
        if self.results.get("node_version", {}).get("status") == "missing":
            print_info("Node.js未安装 - Playwright抓包功能不可用")
        elif self.missing_node:
            print_warning(f"缺失Node.js包: {', '.join(self.missing_node)}")

        # 浏览器检查
        if not self.available_browsers:
            print_warning("未检测到浏览器 - 自动化功能可能受限")
            all_ok = False

        if all_ok:
            print_success("\n✓ 环境检测通过！所有必需依赖已就绪。")
        else:
            print_warning("\n⚠ 环境存在问题，建议安装缺失依赖。")

        # 自动安装选项
        if critical_missing and self.auto_install:
            print_info("\n开始自动安装缺失依赖...")
            self.install_python_packages(self.missing_python)
            self.install_node_packages(skill_dir)

            # 如果安装了playwright，安装浏览器
            if "playwright" in self.missing_python or "playwright" in self.missing_node:
                self.install_playwright_browsers()

        # 保存报告
        if output_file:
            self.save_report(skill_dir / output_file)

        return all_ok


def main():
    import argparse

    parser = argparse.ArgumentParser(description="URL Analyzer SDK Generator 环境检测工具")
    parser.add_argument("--auto-install", action="store_true", help="自动安装缺失依赖")
    parser.add_argument("--output", type=str, default="environment-report.json", help="输出报告文件名")
    parser.add_argument("--json", action="store_true", help="仅输出JSON报告")
    parser.add_argument("--quiet", action="store_true", help="静默模式，仅显示关键信息")

    args = parser.parse_args()

    skill_dir = Path(__file__).parent.parent

    if args.json:
        # 仅JSON输出模式 - 完全静默
        checker = EnvironmentChecker(auto_install=False, silent=True)
        checker.check_python_env()
        checker.check_node_env(skill_dir)
        checker.check_browsers()
        report = checker.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["all_ok"] else 1

    if args.quiet:
        # 静默模式，只输出关键状态
        checker = EnvironmentChecker(auto_install=args.auto_install, silent=True)
        checker.check_python_env()
        checker.check_node_env(skill_dir)
        checker.check_browsers()

        if checker.missing_python:
            print(f"MISSING_PYTHON: {','.join(checker.missing_python)}")
        if checker.missing_node:
            print(f"MISSING_NODE: {','.join(checker.missing_node)}")
        if not checker.available_browsers:
            print("MISSING_BROWSERS: all")

        if not checker.missing_python and checker.available_browsers:
            print("ENV_OK")
            return 0
        return 1

    # 正常模式
    checker = EnvironmentChecker(auto_install=args.auto_install, silent=False)
    all_ok = checker.run(skill_dir, args.output)

    if not all_ok and not args.auto_install:
        print_info("\n提示: 使用 --auto-install 参数自动安装缺失依赖")
        print_info("示例: python check-environment.py --auto-install")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())