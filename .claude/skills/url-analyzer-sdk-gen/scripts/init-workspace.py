#!/usr/bin/env python3
"""
逆向项目工作目录初始化脚本
在用户项目路径下创建标准化的逆向分析工作目录
自动复制必要的脚本、Hook文件到项目目录

使用方式:
python init-workspace.py --url "https://example.com/api" --project-root "/path/to/project"

输出:
创建完整的工作目录结构，包含配置文件和脚本文件
"""

import os
import json
import argparse
import re
import shutil
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path
from typing import Any


# 获取skill目录路径（脚本所在目录的父目录）
SKILL_DIR = Path(__file__).parent.parent.resolve()


class WorkspaceInitializer:
    """工作目录初始化器"""

    # 标准目录结构定义
    DIRECTORY_STRUCTURE = {
        'browser-data': '浏览器用户数据目录（可选，用于免登录抓包）',
        'capture-data': {
            'har': 'HAR格式完整抓包数据',
            'xhr': 'XHR/Fetch请求JSON数据',
            'js': 'JS文件内容',
            'headers': '请求头分析数据'
        },
        'analysis': {
            'search-results': 'JS搜索结果'
        },
        'hook-output': {
            'intercept': 'Hook拦截分析结果'
        },
        'scripts': '逆向分析脚本（从skill目录复制）',
        'hooks': 'Hook脚本存放目录',
        'output': {
            'sdk': {
                'python': 'Python SDK代码',
                'javascript': 'JavaScript SDK代码',
                'java': 'Java SDK代码'
            }
        },
        'validation': '验证结果存放目录'
    }

    def __init__(self, url: str, project_root: str | None = None, preferences: dict[str, Any] | None = None):
        """
        初始化

        Args:
            url: 目标URL
            project_root: 项目根目录，默认为当前工作目录
            preferences: 用户选择的抓包和SDK偏好配置
        """
        self.url = url
        self.project_root = project_root or os.getcwd()
        self.preferences = preferences or {}
        self.parsed_url = urlparse(url)
        self.site_name = self._extract_site_name()
        self.workspace_path: str | None = None

    def _require_workspace_path(self) -> str:
        if self.workspace_path is None:
            raise RuntimeError("workspace_path 尚未初始化")
        return self.workspace_path

    def _extract_site_name(self) -> str:
        """
        从URL提取站点名称

        Examples:
            https://api.example.com/v2/data -> example-api
            https://www.test-site.com/api -> test-site
        """
        hostname = self.parsed_url.hostname or 'unknown'

        # 移除常见前缀
        hostname = re.sub(r'^(www\.|api\.|m\.)', '', hostname)

        # 提取主域名
        parts = hostname.split('.')
        if len(parts) >= 2:
            main_name = parts[0]
        else:
            main_name = hostname

        # 清理特殊字符
        main_name = re.sub(r'[^a-zA-Z0-9]', '-', main_name)

        # 如果有api路径，添加后缀
        if 'api' in self.parsed_url.path.lower():
            main_name = f"{main_name}-api"

        return main_name.lower()

    def _create_directory_structure(self, base_path: str, structure: dict, indent: int = 0):
        """
        递归创建目录结构

        Args:
            base_path: 基础路径
            structure: 目录结构字典
            indent: 缩进级别（用于日志）
        """
        for name, content in structure.items():
            dir_path = os.path.join(base_path, name)
            os.makedirs(dir_path, exist_ok=True)

            prefix = "  " * indent
            if isinstance(content, dict):
                print(f"{prefix}├── {name}/")
                self._create_directory_structure(dir_path, content, indent + 1)
            else:
                print(f"{prefix}├── {name}/  # {content}")

    def _create_project_config(self) -> dict:
        """
        创建项目配置文件
        """
        workspace_path = self._require_workspace_path()
        browser_data_path = os.path.join(workspace_path, "browser-data")
        user_preferences = {
            "capture_tool": self.preferences.get("capture_tool", "drissionpage"),
            "headless": self.preferences.get("headless", True),
            "browser_type": self.preferences.get("browser_type", "chrome"),
            "browser_data_dir": self.preferences.get("browser_data_dir") or browser_data_path,
            "use_custom_browser_data": self.preferences.get("use_custom_browser_data", False),
            "login_required": self.preferences.get("login_required", False),
            "sdk_languages": self.preferences.get("sdk_languages", ["python"])
        }
        config: dict[str, Any] = {
            "project_info": {
                "name": self.site_name,
                "url": self.url,
                "hostname": self.parsed_url.hostname,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "status": "initialized"
            },
            "paths": {
                "workspace": workspace_path,
                "browser_data": browser_data_path,
                "capture_data": os.path.join(workspace_path, "capture-data"),
                "analysis": os.path.join(workspace_path, "analysis"),
                "hook_output": os.path.join(workspace_path, "hook-output"),
                "scripts": os.path.join(workspace_path, "scripts"),
                "hooks": os.path.join(workspace_path, "hooks"),
                "output": os.path.join(workspace_path, "output"),
                "validation": os.path.join(workspace_path, "validation")
            },
            "scripts": {
                "environment_checker": "scripts/check-environment.py",
                "drissionpage_capture": "scripts/drissionpage-capture.py",
                "playwright_capture": "scripts/playwright-capture.js",
                "page_type_detector": "scripts/page-type-detector.py",
                "crypto_detector": "scripts/crypto-param-detector.py",
                "js_search": "scripts/js-search-tool.py",
                "webpack_module_extractor": "scripts/webpack-module-extractor.py",
                "sdk_validator": "scripts/sdk-validator.py"
            },
            "url_info": {
                "scheme": self.parsed_url.scheme,
                "hostname": self.parsed_url.hostname,
                "port": self.parsed_url.port,
                "path": self.parsed_url.path,
                "query": self.parsed_url.query
            },
            "analysis_progress": {
                "environment_checked": False,
                "page_type_detected": False,
                "capture_completed": False,
                "crypto_analyzed": False,
                "hook_analyzed": False,
                "reverse_completed": False,
                "sdk_generated": False,
                "validation_passed": False
            },
            "findings": {
                "page_type": None,
                "encrypted_params": [],
                "crypto_algorithm": None,
                "sign_logic": None,
                "key_modules": [],
                "verification_layers": {
                    "signature_match": False,
                    "real_api_ok": False,
                    "decryption_ok": False
                }
            },
            "user_preferences": user_preferences
        }
        return config

    def _write_text_file(self, file_path: str, content: str, overwrite: bool = True):
        if not overwrite and os.path.exists(file_path):
            print(f"[SKIP] 保留现有文件: {file_path}")
            return
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _write_json_file(self, file_path: str, content: dict[str, Any], overwrite: bool = True):
        if not overwrite and os.path.exists(file_path):
            print(f"[SKIP] 保留现有文件: {file_path}")
            return
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

    def _create_gitignore(self):
        """创建.gitignore文件"""
        gitignore_content = """# 逆向项目忽略配置

# 抓包数据（可能包含敏感信息）
capture-data/har/*.har
capture-data/xhr/*.json

# JS文件（体积大）
capture-data/js/*.js

# 验证日志
validation/*.log

# Python缓存
__pycache__/
*.py[cod]
*$py.class
*.so

# 敏感配置
secrets.json
.env
"""
        workspace_path = self._require_workspace_path()
        gitignore_path = os.path.join(workspace_path, ".gitignore")
        self._write_text_file(gitignore_path, gitignore_content)

    def _create_readme(self):
        """创建初始README"""
        readme_content = f"""# {self.site_name} 逆向分析项目

## 项目信息
- **目标URL**: {self.url}
- **创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **状态**: 初始化完成

## 目录结构
```
{self.site_name}/
├── browser-data/      # 浏览器用户数据（可选）
├── capture-data/      # 抓包原始数据
│   ├── har/           # HAR格式抓包
│   ├── xhr/           # XHR/Fetch请求JSON
│   ├── js/            # JS文件内容
│   └── headers/       # 请求头分析
├── analysis/          # 分析过程数据
│   ├── page-type.json # 页面类型判定
│   ├── crypto-analysis.json # 加密参数分析
│   ├── reverse-notes.md     # 逆向分析笔记
│   └── search-results/      # JS搜索结果
├── hook-output/       # Hook拦截结果
│   └── intercept/     # Hook分析输出
├── scripts/           # 逆向分析脚本（可直接使用）
│   ├── check-environment.py      # 环境检测
│   ├── drissionpage-capture.py   # DrissionPage抓包
│   ├── playwright-capture.js     # Playwright抓包
│   ├── page-type-detector.py     # 页面类型检测
│   ├── crypto-param-detector.py  # 加密参数检测
│   ├── js-search-tool.py         # JS关键词搜索
│   ├── webpack-module-extractor.py # Webpack模块提取
│   ├── sdk-validator.py          # SDK验证
│   └── output-templates-generator.py # 输出模板生成
├── hooks/             # Hook脚本
│   ├── all-in-one-hook.js  # 综合Hook
│   ├── xhr-hook.js         # XHR拦截
│   ├── fetch-hook.js       # Fetch拦截
│   ├── crypto-hook.js      # 加密拦截
│   └── debug-hook.js       # 调试工具
├── output/            # 最终输出物
│   ├── analysis-report.md  # 分析报告
│   ├── sdk-document.md     # SDK文档
│   ├── README.md           # 使用说明
│   └── sdk/                # SDK代码
│       ├── python/
│       ├── javascript/
│       └── java/
└── validation/        # 验证结果
```

## 分析进度
- [ ] 环境检测
- [ ] 页面类型检测
- [ ] 网络抓包
- [ ] 加密参数分析
- [ ] Hook调试/模块提取
- [ ] SDK生成
- [ ] 三层验证

## 推荐工作流
在项目目录内执行以下命令：

```bash
# 进入项目目录
cd {self.workspace_path}

# 0. 环境检测
python scripts/check-environment.py --json

# 1. 检测页面类型
python scripts/page-type-detector.py "{self.url}"

# 2. 网络抓包（推荐使用DrissionPage）
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data"

# 3. 分析加密参数
python scripts/crypto-param-detector.py capture-data/xhr/api-requests.json

# 4. 搜索JS关键词
python scripts/js-search-tool.py --js-dir capture-data/js/ --keywords "encrypt,sign,md5,sha,portal-sign"

# 5. 提取Webpack模块（先定位签名模块，再追踪依赖模块）
python scripts/webpack-module-extractor.py capture-data/js/app.js --find-sign-func
python scripts/webpack-module-extractor.py capture-data/js/app.js --extract-module b775
python scripts/webpack-module-extractor.py capture-data/js/app.js --extract-module a078

# 6. Hook注入调试（存在加密参数时）
python scripts/hook-inject-drissionpage.py --url "{self.url}" --hook "all-in-one-hook.js" --output "./hook-output" --wait 30

# 7. 生成SDK后执行真实验证
python scripts/sdk-validator.py --sdk-path output/sdk/python/ --test-url "{self.url}"
```

## 关键经验
- 不要默认把签名算法当作 `key=value&key2=value2`，必须按JS源码逐字复现拼接逻辑。
- 默认优先使用 `curl_cffi` 发起真实请求，避免标准 `requests` 被 WAF/TLS 指纹拦截。
- Key/IV/Salt 常常不在签名函数所在模块，而在其 `n(\"moduleId\")` 依赖模块中。
- SDK 只有在 **签名匹配 + 真实API成功 + 解密结果正确** 三层都通过后才算可用。

## 注意事项
- 抓包数据可能包含敏感信息，请勿直接提交到公开仓库。
- SDK仅供学习研究使用。
- DrissionPage默认继承Chrome用户数据，实现免登录抓包。
- 如需全新会话，使用 `--no-user-data` 参数。
"""
        workspace_path = self._require_workspace_path()
        readme_path = os.path.join(workspace_path, "README.md")
        self._write_text_file(readme_path, readme_content, overwrite=False)

    def _create_analysis_templates(self):
        """创建分析模板文件"""

        # 页面类型判定结果模板
        page_type_template = {
            "url": self.url,
            "page_type": None,
            "confidence": 0.0,
            "evidence": [],
            "recommendation": None,
            "analyzed_at": None
        }
        workspace_path = self._require_workspace_path()
        page_type_path = os.path.join(workspace_path, "analysis", "page-type.json")
        self._write_json_file(page_type_path, page_type_template, overwrite=False)

        # 加密分析结果模板
        crypto_template = {
            "url": self.url,
            "has_encryption": False,
            "encrypted_params": [],
            "signature_params": [],
            "timestamp_params": [],
            "encryption_patterns": [],
            "reverse_recommendations": [],
            "analyzed_at": None
        }
        crypto_path = os.path.join(workspace_path, "analysis", "crypto-analysis.json")
        self._write_json_file(crypto_path, crypto_template, overwrite=False)

        # 逆向笔记模板
        reverse_notes = f"""# 逆向分析笔记

## 目标URL
{self.url}

## 分析步骤

### 1. 页面类型判定
- 判定结果:
- 判定依据:
- 置信度:

### 2. 网络抓包分析
- XHR请求数量:
- 关键API列表:
- JS文件数量:

### 3. 加密参数识别
- 加密参数列表:
- 加密特征:

### 4. 加密函数定位
- 搜索关键词:
- 定位结果:
- 函数位置:

### 5. 算法分析
- 加密算法:
- 签名逻辑:
- 密钥/Secret:

## 遇到的问题
1.
2.

## 解决方案
1.
2.

## 最终结论

"""
        reverse_notes_path = os.path.join(workspace_path, "analysis", "reverse-notes.md")
        self._write_text_file(reverse_notes_path, reverse_notes, overwrite=False)

    def _copy_file_if_missing(self, src_path: Path, dst_path: Path, label: str):
        if dst_path.exists():
            print(f"  ├── [SKIP] 保留现有{label}: {dst_path.name}")
            return False
        shutil.copy2(src_path, dst_path)
        print(f"  ├── 复制{label}: {dst_path.name}")
        return True

    def _copy_scripts_to_workspace(self):
        """
        将skill目录下的scripts脚本复制到项目工作目录
        使逆向项目能够独立使用这些脚本
        """
        skill_scripts_dir = SKILL_DIR / "scripts"
        workspace_scripts_dir = Path(self.workspace_path) / "scripts"

        if not skill_scripts_dir.exists():
            print(f"[WARNING] Skill scripts目录不存在: {skill_scripts_dir}")
            return

        # 要复制的脚本文件列表
        scripts_to_copy = [
            'check-environment.py',
            'drissionpage-capture.py',
            'playwright-capture.js',
            'page-type-detector.py',
            'crypto-param-detector.py',
            'js-search-tool.py',
            'webpack-module-extractor.py',
            'hook-inject-drissionpage.py',
            'hook-inject-playwright.py',
            'manual-login.py',
            'sdk-validator.py',
            'output-templates-generator.py'
        ]

        copied_count = 0
        for script_name in scripts_to_copy:
            src_path = skill_scripts_dir / script_name
            dst_path = workspace_scripts_dir / script_name

            if src_path.exists():
                if self._copy_file_if_missing(src_path, dst_path, '脚本'):
                    copied_count += 1
            else:
                print(f"  ├── [SKIP] 脚本不存在: {script_name}")

        print(f"[SUCCESS] 复制了 {copied_count} 个脚本到 {workspace_scripts_dir}")

    def _copy_hooks_to_workspace(self):
        """
        将skill目录下的hooks脚本复制到项目工作目录
        """
        skill_hooks_dir = SKILL_DIR / "hooks"
        workspace_hooks_dir = Path(self.workspace_path) / "hooks"

        if not skill_hooks_dir.exists():
            print(f"[WARNING] Skill hooks目录不存在: {skill_hooks_dir}")
            return

        # 要复制的hook文件列表
        hooks_to_copy = [
            'xhr-hook.js',
            'fetch-hook.js',
            'crypto-hook.js',
            'debug-hook.js',
            'all-in-one-hook.js'
        ]

        copied_count = 0
        for hook_name in hooks_to_copy:
            src_path = skill_hooks_dir / hook_name
            dst_path = workspace_hooks_dir / hook_name

            if src_path.exists():
                if self._copy_file_if_missing(src_path, dst_path, 'Hook'):
                    copied_count += 1
            else:
                print(f"  ├── [SKIP] Hook不存在: {hook_name}")

        print(f"[SUCCESS] 复制了 {copied_count} 个Hook到 {workspace_hooks_dir}")

    def initialize(self) -> str:
        """
        执行初始化

        Returns:
            工作目录路径
        """
        # 创建基础目录
        reverse_projects_dir = os.path.join(self.project_root, "reverse-projects")
        os.makedirs(reverse_projects_dir, exist_ok=True)

        # 创建项目工作目录
        self.workspace_path = os.path.join(reverse_projects_dir, self.site_name)
        if os.path.exists(self.workspace_path):
            print(f"[WARNING] 工作目录已存在: {self.workspace_path}")
            print("[INFO] 将在现有目录上继续工作...")
        else:
            os.makedirs(self.workspace_path, exist_ok=True)
            print(f"[SUCCESS] 创建工作目录: {self.workspace_path}")

        print(f"\n项目: {self.site_name}")
        print(f"URL: {self.url}")
        print("\n目录结构:")
        self._create_directory_structure(self.workspace_path, self.DIRECTORY_STRUCTURE)

        # 创建配置文件
        config = self._create_project_config()
        config_path = os.path.join(self.workspace_path, "project-config.json")
        self._write_json_file(config_path, config, overwrite=False)
        print(f"\n[CONFIG] 配置文件: {config_path}")

        # 创建辅助文件
        self._create_gitignore()
        self._create_readme()
        self._create_analysis_templates()

        # 复制脚本和Hook文件到项目目录
        print("\n[SCRIPTS] 复制分析脚本到项目目录...")
        self._copy_scripts_to_workspace()
        print("\n[HOOKS] 复制Hook脚本到项目目录...")
        self._copy_hooks_to_workspace()

        print("\n" + "="*60)
        print("初始化完成！")
        print("="*60)
        print(f"\n工作目录: {self.workspace_path}")
        print("\n下一步操作（在项目目录内执行）:")
        print(f"  cd {self.workspace_path}")
        print(f"  1. 检测页面类型: python scripts/page-type-detector.py \"{self.url}\"")
        print(f"  2. 网络抓包(DrissionPage): python scripts/drissionpage-capture.py --url \"{self.url}\" --output \"./capture-data\"")
        print(f"  3. 网络抓包(Playwright): node scripts/playwright-capture.js \"{self.url}\" \"./capture-data\"")

        return self.workspace_path


def main():
    parser = argparse.ArgumentParser(
        description='初始化逆向项目工作目录',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python init-workspace.py --url "https://api.example.com/v1/data"
  python init-workspace.py --url "https://example.com" --project-root "/home/user/myproject"
        """
    )

    parser.add_argument(
        '--url', '-u',
        required=True,
        help='目标URL'
    )

    parser.add_argument(
        '--project-root', '-p',
        default=None,
        help='项目根目录（默认为当前工作目录）'
    )

    parser.add_argument(
        '--capture-tool',
        choices=['drissionpage', 'playwright'],
        default='drissionpage',
        help='抓包工具'
    )

    parser.add_argument(
        '--browser',
        choices=['chrome', 'edge', 'chromium', 'firefox'],
        default='chrome',
        help='浏览器类型'
    )

    parser.add_argument(
        '--browser-data',
        choices=['project', 'custom'],
        default='project',
        help='浏览器数据目录来源'
    )

    parser.add_argument(
        '--browser-data-dir',
        default=None,
        help='自定义浏览器数据目录'
    )

    parser.add_argument(
        '--mode',
        choices=['headless', 'headed'],
        default='headless',
        help='浏览器执行模式'
    )

    parser.add_argument(
        '--login',
        choices=['yes', 'no'],
        default='no',
        help='是否需要登录'
    )

    parser.add_argument(
        '--languages',
        default='python',
        help='SDK语言，逗号分隔，例如 python,javascript'
    )

    args = parser.parse_args()

    preferences = {
        "capture_tool": args.capture_tool,
        "headless": args.mode == 'headless',
        "browser_type": args.browser,
        "browser_data_dir": args.browser_data_dir,
        "use_custom_browser_data": args.browser_data == 'custom',
        "login_required": args.login == 'yes',
        "sdk_languages": [language.strip() for language in args.languages.split(',') if language.strip()]
    }

    initializer = WorkspaceInitializer(args.url, args.project_root, preferences)
    workspace_path = initializer.initialize()

    # 输出JSON格式结果供其他脚本调用
    result = {
        "success": True,
        "workspace_path": workspace_path,
        "site_name": initializer.site_name,
        "url": args.url
    }
    print(f"\n[JSON OUTPUT]\n{json.dumps(result, indent=2)}")


if __name__ == '__main__':
    main()