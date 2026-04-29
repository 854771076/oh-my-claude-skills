# 工作目录规范

## 目录结构

**必须** 在用户当前项目路径下创建逆向工作目录：

```
{project_root}/reverse-projects/
└── {site_name}/                    # 从URL提取的站点名称
    ├── capture-data/               # 抓包原始数据
    │   ├── har/                    # HAR格式完整抓包
    │   ├── xhr/                    # XHR/Fetch请求JSON
    │   ├── js/                     # JS文件内容
    │   └── headers/                # 请求头分析
    ├── analysis/                   # 分析过程数据
    │   ├── page-type.json          # 页面类型判定结果
    │   ├── crypto-analysis.json    # 加密参数分析结果
    │   ├── reverse-notes.md        # 逆向分析笔记
    │   └── search-results/         # JS搜索结果
    │       ├── encrypt-functions.json
    │       ├── sign-functions.json
    │       └── crypto-keywords.json
    ├── scripts/                    # 逆向分析脚本（自动复制）
    │   ├── check-environment.py    # 环境检测与自动安装脚本
    │   ├── drissionpage-capture.py # DrissionPage抓包脚本
    │   ├── playwright-capture.js   # Playwright抓包脚本
    │   ├── hook-inject-drissionpage.py # DrissionPage Hook注入调试脚本
    │   ├── hook-inject-playwright.py   # Playwright Hook注入调试脚本
    │   ├── page-type-detector.py   # 页面类型检测
    │   ├── crypto-param-detector.py# 加密参数检测
    │   ├── js-search-tool.py       # JS关键词搜索
    │   ├── sdk-validator.py        # SDK验证脚本
    │   ├── manual-login.py         # 手动登录脚本
    │   └── output-templates-generator.py # 输出模板生成
    ├── hooks/                      # Hook脚本（自动复制）
    │   ├── xhr-hook.js             # XHR拦截Hook
    │   ├── fetch-hook.js           # Fetch拦截Hook
    │   ├── crypto-hook.js          # 加密函数Hook
    │   ├── debug-hook.js           # 调试Hook
    │   └── all-in-one-hook.js      # 综合Hook
    ├── output/                     # 最终输出物
    │   ├── analysis-report.md      # 逆向分析报告
    │   ├── sdk-document.md         # SDK接口说明文档
    │   ├── README.md               # 使用说明
    │   └── sdk/                    # SDK代码
    │       ├── python/
    │       ├── javascript/
    │       └── java/
    └── validation/                 # 验证结果
        ├── test-results.json       # 测试结果
        └── verify-log.md           # 验证日志
```

## 初始化脚本

使用 `scripts/init-workspace.py` 创建标准化目录结构，并自动复制所需脚本：

```bash
# 初始化工作目录（会自动复制scripts和hooks到项目目录）
python .claude/skills/url-analyzer-sdk-gen/scripts/init-workspace.py \
    --url "https://example.com/api" \
    --project-root "{当前项目路径}"

# 初始化后，在项目目录内可直接使用脚本
cd reverse-projects/{site_name}
python scripts/drissionpage-capture.py --url "https://example.com/api" --output "./capture-data"
```

## 项目配置文件

创建 `project-config.json`：

```json
{
  "project_info": {
    "url": "https://example.com/api",
    "site_name": "example-api",
    "created_at": "2026-04-09T10:00:00"
  },
  "paths": {
    "workspace": "reverse-projects/example-api",
    "scripts": "reverse-projects/example-api/scripts",
    "hooks": "reverse-projects/example-api/hooks",
    "browser_data": "reverse-projects/example-api/browser-data"
  },
  "scripts": {
    "drissionpage_capture": "scripts/drissionpage-capture.py",
    "playwright_capture": "scripts/playwright-capture.js"
  },
  "user_preferences": {
    "capture_tool": "drissionpage",
    "headless": true,
    "browser_type": "chrome",
    "browser_path": null,
    "browser_data_dir": "reverse-projects/example-api/browser-data",
    "use_custom_browser_data": false,
    "profile_dir": "Default",
    "sdk_languages": ["python"]
  }
}
```