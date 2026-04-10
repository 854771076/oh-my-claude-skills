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
import sys
import json
import argparse
import re
import shutil
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path


# 获取skill目录路径（脚本所在目录的父目录）
SKILL_DIR = Path(__file__).parent.parent.resolve()


class WorkspaceInitializer:
    """工作目录初始化器"""

    # 标准目录结构定义
    DIRECTORY_STRUCTURE = {
        'capture-data': {
            'har': 'HAR格式完整抓包数据',
            'xhr': 'XHR/Fetch请求JSON数据',
            'js': 'JS文件内容',
            'headers': '请求头分析数据'
        },
        'analysis': {
            'search-results': 'JS搜索结果'
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

    def __init__(self, url: str, project_root: str = None):
        """
        初始化

        Args:
            url: 目标URL
            project_root: 项目根目录，默认为当前工作目录
        """
        self.url = url
        self.project_root = project_root or os.getcwd()
        self.parsed_url = urlparse(url)
        self.site_name = self._extract_site_name()
        self.workspace_path = None

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
        config = {
            "project_info": {
                "name": self.site_name,
                "url": self.url,
                "hostname": self.parsed_url.hostname,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "status": "initialized"
            },
            "paths": {
                "workspace": self.workspace_path,
                "capture_data": os.path.join(self.workspace_path, "capture-data"),
                "analysis": os.path.join(self.workspace_path, "analysis"),
                "scripts": os.path.join(self.workspace_path, "scripts"),
                "hooks": os.path.join(self.workspace_path, "hooks"),
                "output": os.path.join(self.workspace_path, "output"),
                "validation": os.path.join(self.workspace_path, "validation")
            },
            "scripts": {
                "drissionpage_capture": "scripts/drissionpage-capture.py",
                "playwright_capture": "scripts/playwright-capture.js",
                "page_type_detector": "scripts/page-type-detector.py",
                "crypto_detector": "scripts/crypto-param-detector.py",
                "js_search": "scripts/js-search-tool.py",
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
                "page_type_detected": False,
                "capture_completed": False,
                "crypto_analyzed": False,
                "reverse_completed": False,
                "sdk_generated": False,
                "validation_passed": False
            },
            "findings": {
                "page_type": None,
                "encrypted_params": [],
                "crypto_algorithm": None,
                "sign_logic": None
            }
        }
        return config

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
        gitignore_path = os.path.join(self.workspace_path, ".gitignore")
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)

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
├── scripts/           # 逆向分析脚本（可直接使用）
│   ├── drissionpage-capture.py  # DrissionPage抓包
│   ├── playwright-capture.js    # Playwright抓包
│   ├── page-type-detector.py    # 页面类型检测
│   ├── crypto-param-detector.py # 加密参数检测
│   ├── js-search-tool.py        # JS关键词搜索
│   ├── sdk-validator.py         # SDK验证
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
- [ ] 页面类型检测
- [ ] 网络抓包
- [ ] 加密参数分析
- [ ] 逆向分析
- [ ] SDK生成
- [ ] 验证测试

## 快速开始
在项目目录内执行以下命令：

```bash
# 进入项目目录
cd {self.workspace_path}

# 1. 检测页面类型
python scripts/page-type-detector.py "{self.url}"

# 2. 网络抓包（推荐使用DrissionPage）
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data"

# 或使用Playwright抓包
node scripts/playwright-capture.js "{self.url}" "./capture-data"

# 3. 分析加密参数
python scripts/crypto-param-detector.py capture-data/xhr/api-requests.json

# 4. 搜索JS关键词
python scripts/js-search-tool.py --js-dir capture-data/js/

# 5. 验证SDK
python scripts/sdk-validator.py --sdk-path output/sdk/python/
```

## DrissionPage抓包选项
```bash
# 基本用法
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data"

# 无头模式（后台运行）
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data"

# 有头模式（显示浏览器，方便调试）
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data" --headed

# 使用Edge浏览器
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data" --browser edge

# 继承用户数据（免登录抓包）
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data" --user-data-dir "C:/Users/xxx/AppData/Local/Google/Chrome/User Data"

# 不继承用户数据（全新会话）
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data" --no-user-data

# 查看详细日志
python scripts/drissionpage-capture.py --url "{self.url}" --output "./capture-data" --verbose
```

## Hook脚本使用
Hook脚本用于在浏览器中拦截和分析请求：

```javascript
// 在浏览器控制台注入 hooks/all-in-one-hook.js
// 可用命令：
__hook_export__()           // 导出拦截数据
__hook_clear__()            // 清空拦截数据
__hook_set_debug__(bool)    // 开关debugger
__fix_random__(timestamp)   // 固定随机变量
```

## 注意事项
- 抓包数据可能包含敏感信息，请勿直接提交到公开仓库
- SDK仅供学习研究使用
- DrissionPage默认继承Chrome用户数据，实现免登录抓包
- 如需全新会话，使用 --no-user-data 参数
"""
        readme_path = os.path.join(self.workspace_path, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

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
        with open(os.path.join(self.workspace_path, "analysis", "page-type.json"), 'w') as f:
            json.dump(page_type_template, f, indent=2)

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
        with open(os.path.join(self.workspace_path, "analysis", "crypto-analysis.json"), 'w') as f:
            json.dump(crypto_template, f, indent=2)

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
        with open(os.path.join(self.workspace_path, "analysis", "reverse-notes.md"), 'w') as f:
            f.write(reverse_notes)

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
            'drissionpage-capture.py',
            'playwright-capture.js',
            'page-type-detector.py',
            'crypto-param-detector.py',
            'js-search-tool.py',
            'sdk-validator.py',
            'output-templates-generator.py'
        ]

        copied_count = 0
        for script_name in scripts_to_copy:
            src_path = skill_scripts_dir / script_name
            dst_path = workspace_scripts_dir / script_name

            if src_path.exists():
                shutil.copy2(src_path, dst_path)
                copied_count += 1
                print(f"  ├── 复制脚本: {script_name}")
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
                shutil.copy2(src_path, dst_path)
                copied_count += 1
                print(f"  ├── 复制Hook: {hook_name}")
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
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
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
        print(f"\n下一步操作（在项目目录内执行）:")
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

    args = parser.parse_args()

    initializer = WorkspaceInitializer(args.url, args.project_root)
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