---
name: url-analyzer-sdk-gen
description: URL分析SDK生成器V4 - 输入URL自动判断静态/动态页面，静态页面生成数据解析代码，动态页面分析加密参数并生成SDK或启动逆向工作流，完整输出分析报告和SDK文档，支持DrissionPage(默认)和Playwright双引擎，支持手动登录流程
---

# URL Analyzer & SDK Generator V4.0

## 概述
这个skill实现了一个完整的URL逆向分析与SDK生成工作流：
1. **输入URL** → 自动判断静态/动态页面
2. **静态页面** → 用户补充解析区域 → 生成请求和数据解析代码
3. **动态页面** → 抓包工具捕获请求 → 分析加密参数
   - 有加密 → 启动逆向工作流分析加密参数
   - 无加密 → 生成多语言SDK（Python/JS/Java等）
4. **完整输出** → 分析报告 + SDK文档 + README + 验证结果

## 抓包引擎
- **DrissionPage (默认)** - 轻量级，结合requests和selenium优点，CDP协议抓包，资源占用低
- **Playwright** - 功能强大，支持多浏览器，持久化上下文，适合复杂场景

## V4.0 更新
- ✅ 修复JS文件捕获问题（resourceType大小写兼容）
- ✅ 用户数据目录迁移到项目内，不再继承本地浏览器数据
- ✅ 新增手动登录脚本，支持在抓包前完成登录
- ✅ 新增单元测试

## 触发条件
- 用户输入 `/analyze-url` 命令
- 用户输入包含URL格式（如 `https://example.com/...`）且上下文暗示需要分析

## 前置配置询问

**必须首先询问用户以下配置项**：

### 1. 抓包工具选择
```
使用哪种抓包工具？
- DrissionPage (推荐) - 轻量级，CDP协议，资源占用低
- Playwright - 功能强大，支持多浏览器，持久化上下文，适合复杂场景
```

### 2. 浏览器数据目录位置（新增）
```
浏览器用户数据目录存放在哪里？
- 项目目录下 (推荐) - {project_root}/reverse-projects/{site_name}/browser-data/
  - 数据独立隔离，不继承本地浏览器数据
  - 需要在抓包前手动登录获取登录态
- 自定义目录 - 您可以指定其他位置
  - 例如：C:\Users\xxx\AppData\Local\Google\Chrome\User Data
  - 可以继承已有的浏览器登录态
```

### 3. 浏览器选择
```
使用哪种浏览器？
- Chrome (推荐) - 使用本地Chrome浏览器
- Edge - 使用本地Edge浏览器
- Chromium (仅Playwright) - 自动下载的Chromium，无需本地安装
- Firefox (仅Playwright) - 使用本地或自动下载的Firefox

注意：
- DrissionPage: 支持Chrome和Edge
- Playwright: 支持所有浏览器选项
- 选择本地浏览器时，请确保浏览器已安装
```

### 4. 登录需求询问（新增）
```
目标网站是否需要登录才能获取完整数据？
- 需要登录 - 将打开浏览器让您手动登录，登录完成后自动开始抓包
- 不需要登录 - 直接开始抓包
```

### 5. 执行模式
```
是否使用无头模式执行？
- 无头模式 (推荐) - 后台运行，不显示浏览器窗口，速度快
- 有头模式 - 显示浏览器窗口，方便调试和观察页面行为
```

### 6. SDK语言选择
```
需要生成哪些语言的SDK？(可多选)
- [x] Python - 使用requests/aiohttp
- [ ] JavaScript/Node.js - 使用axios/fetch
- [ ] Java - 使用OkHttp
- [ ] Go - 使用net/http
```

**配置保存**：将用户选择保存到 `project-config.json` 的 `user_preferences` 字段。

## 登录流程（新增）

当用户选择"需要登录"时：

1. **创建用户数据目录**
   ```
   {project_root}/reverse-projects/{site_name}/browser-data/
   ```

2. **执行手动登录脚本**
   ```bash
   python scripts/manual-login.py --url "{url}" --browser {browser} --user-data-dir "./browser-data"
   ```

3. **用户手动登录**
   - 脚本打开浏览器访问目标网站
   - 用户在浏览器中完成登录操作
   - 登录完成后关闭浏览器

4. **确认登录状态**
   ```
   请确认是否已成功登录？
   - 已成功登录 - 开始抓包
   - 登录失败 - 重新尝试登录
   ```

5. **后续抓包使用同一用户数据目录**
   ```bash
   python scripts/drissionpage-capture.py --url "{url}" --user-data-dir "./browser-data" ...
   ```

## 工作目录规范

### 目录初始化
**必须** 在用户当前项目路径下创建逆向工作目录，并自动复制所需脚本：

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
    │   ├── drissionpage-capture.py # DrissionPage抓包脚本
    │   ├── playwright-capture.js   # Playwright抓包脚本
    │   ├── page-type-detector.py   # 页面类型检测
    │   ├── crypto-param-detector.py# 加密参数检测
    │   ├── js-search-tool.py       # JS关键词搜索
    │   ├── sdk-validator.py        # SDK验证脚本
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

### 工作目录初始化脚本
使用 `scripts/init-workspace.py` 创建标准化目录结构，并自动复制所需脚本：

```bash
# 初始化工作目录（会自动复制scripts和hooks到项目目录）
python .claude/skills/url-analyzer-sdk-gen/scripts/init-workspace.py --url "https://example.com/api" --project-root "{当前项目路径}"

# 初始化后，在项目目录内可直接使用脚本
cd reverse-projects/{site_name}
python scripts/drissionpage-capture.py --url "https://example.com/api" --output "./capture-data"
```

## 工作流程

### Phase 0: 前置配置与工作目录初始化
**必须首先执行**：

1. **询问用户配置**
   使用 `AskUserQuestion` 工具询问：
   - **抓包工具**: DrissionPage/Playwright
   - **浏览器数据目录位置**: 项目目录下(推荐)/自定义目录
   - **浏览器选择**: Chrome/Edge/Chromium/Firefox（Chromium和Firefox仅Playwright有效）
   - **执行模式**: 无头/有头
   - **登录需求**: 需要登录/不需要登录
   - **SDK语言**: Python/JavaScript/Java/Go（多选）

2. **解析URL提取站点名称**（如 `api.example.com` → `example-api`）

3. **在当前项目路径下创建** `reverse-projects/{site_name}/` 目录

4. **初始化完整的子目录结构，并自动复制脚本和Hook文件**
   - 复制 `scripts/` 下的分析脚本到项目 `scripts/` 目录
   - 复制 `hooks/` 下的Hook脚本到项目 `hooks/` 目录

5. **创建配置文件** `project-config.json`，包含：
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

**输出**：工作目录路径 + 项目配置文件 + 已复制的脚本文件

### Phase 1: URL接收与初步分析
**必须执行**（在项目工作目录内）：
1. 提取用户输入的URL
2. 使用项目内的 `scripts/page-type-detector.py` 进行综合判断：
   ```bash
   cd reverse-projects/{site_name}
   python scripts/page-type-detector.py "{url}"
   ```
   - URL扩展名分析（.php/.jsp/.aspx/.do等）
   - 查询参数特征（?id=xxx&action=xxx等）
   - 发送HEAD请求检查响应头（X-Requested-With, Content-Type等）
   - 检查HTML特征（<script>, __NEXT_DATA__, webpack等）
3. 保存分析结果到 `analysis/page-type.json`

**输出**：页面类型判定结果（static/dynamic/ajax-api）+ 初步分析报告

### Phase 2A: 静态页面处理流程
**当判定为静态页面时执行**：

1. **获取页面内容**
   - 使用requests获取HTML
   - 解析DOM结构
   - 保存HTML快照到 `capture-data/html-snapshot.html`

2. **询问用户解析区域**
   ```
   请指定需要解析的数据区域：
   - CSS选择器（如 `.product-list .item`）
   - XPath表达式
   - 或描述数据特征（如"所有商品名称和价格"）
   ```

3. **生成解析代码**
   - 根据用户选择生成对应解析代码
   - 使用 `assets/static-parser-template.py` 作为基础模板
   - 输出SDK到 `output/sdk/python/`

4. **验证与输出**
   - 运行验证测试
   - 输出分析报告、SDK文档、README

### Phase 2B: 动态页面处理流程
**当判定为动态页面时执行**（在项目工作目录内）：

1. **启动抓包工具**
   - 读取 `project-config.json` 中的 `user_preferences.capture_tool` 配置
   - 根据选择执行不同的抓包逻辑（使用项目内脚本）：

   **方案A：DrissionPage抓包（默认）**
   ```bash
   cd reverse-projects/{site_name}
   # 使用项目内脚本抓包
   python scripts/drissionpage-capture.py --url "{url}" --output "./capture-data"

   # 可选参数：
   # --headed       有头模式（显示浏览器）
   # --browser edge 使用Edge浏览器
   # --no-user-data 不继承用户数据
   # --verbose      详细日志
   ```
   - **优势**：轻量级、资源占用低、自动继承Chrome用户数据
   - **适用**：大多数逆向场景，需要登录态的页面

   **方案B：Playwright抓包**
   ```bash
   cd reverse-projects/{site_name}
   node scripts/playwright-capture.js "{url}" "./capture-data"
   ```
   - **优势**：支持多浏览器、功能强大、精确的用户数据控制
   - **适用**：跨浏览器测试、复杂场景

   - 记录XHR/Fetch请求、响应、请求头、参数
   - 保存数据到 `capture-data/har/` 和 `capture-data/xhr/`
   - 下载所有JS文件到 `capture-data/js/`

2. **加密参数检测**
   - 使用项目内脚本 `scripts/crypto-param-detector.py` 分析抓包数据：
   ```bash
   python scripts/crypto-param-detector.py capture-data/xhr/api-requests.json
   ```
   - 保存分析结果到 `analysis/crypto-analysis.json`

3. **JS代码搜索分析**
   - 使用项目内脚本 `scripts/js-search-tool.py` 搜索加密关键词：
   ```bash
   python scripts/js-search-tool.py --js-dir capture-data/js/ --keywords "encrypt,sign,md5,sha,crypto"
   ```
   - 在所有JS文件中搜索：encrypt, sign, crypto, md5, sha, aes, base64
   - 保存搜索结果到 `analysis/search-results/`

4. **分支处理**

   **情况A：无加密参数**
   - 读取 `user_preferences.sdk_languages` 配置
   - 为每种选中的语言生成SDK
   - 输出到 `output/sdk/{language}/`

   **情况B：存在加密参数**
   - 启动逆向工作流（见Phase 3）

### Phase 3: 逆向工作流
**当存在加密参数时执行**：

1. **Hook注入分析**
   使用 `hooks/` 目录下的Hook脚本：
   - **XHR Hook**: 拦截所有XHR请求，记录参数生成过程
   - **Fetch Hook**: 拦截Fetch请求
   - **Crypto Hook**: 拦截加密函数调用（MD5, SHA, AES等）
   - **Debug Hook**: 在关键函数处设置断点

2. **定位加密代码**
   - 分析JS文件，定位加密函数
   - 使用Webpack模块分析工具
   - 结合Hook输出确定加密入口点

3. **自动尝试解密**
   参考 `references/crypto-reverse-guide.md`：
   - 尝试常见加密算法匹配
   - 分析参数生成逻辑
   - 提取关键加密函数

4. **人工介入指引**
   当自动分析失败时，提供详细指引：
   ```
   自动逆向分析遇到困难，需要人工介入：

   1. 建议使用浏览器DevTools调试加密函数
   2. 已定位的JS文件列表：
      - capture-data/js/main.js (包含 encrypt 关键词)
      - capture-data/js/chunk_123.js (包含 sign 关键词)
   3. 关键参数：sign, token
   4. Hook脚本已准备好：
      - hooks/crypto-hook.js 可注入浏览器拦截加密调用

   请提供以下信息以继续分析：
   - 加密函数的JS代码片段
   - 或加密算法的具体描述
   ```

5. **生成逆向SDK**
   - 基于分析结果生成包含加密逻辑的SDK
   - 使用 `assets/reverse-sdk-template.py` 模板

### Phase 4: 验证与输出
**逆向完成后必须执行**：

1. **SDK验证测试**
   - 使用 `scripts/sdk-validator.py` 验证SDK功能
   - 测试签名生成正确性
   - 测试API调用成功率
   - 保存测试结果到 `validation/test-results.json`

2. **输出完整文档**
   - **分析报告**: `output/analysis-report.md`
   - **SDK文档**: `output/sdk-document.md`
   - **README**: `output/README.md`
   - **SDK代码**: `output/sdk/{language}/`

## Hook脚本使用指南

### XHR Hook
注入 `hooks/xhr-hook.js` 拦截XHR请求：
```javascript
// 在浏览器控制台注入
(function() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url) {
        this._url = url;
        this._method = method;
        console.log('[XHR Hook] open:', method, url);
        return originalOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function(data) {
        console.log('[XHR Hook] send:', this._url, data);
        console.trace(); // 打印调用栈
        return originalSend.apply(this, arguments);
    };
})();
```

### Crypto Hook
注入 `hooks/crypto-hook.js` 拦截加密函数：
```javascript
// 拦截CryptoJS调用
(function() {
    if (window.CryptoJS) {
        const originalMD5 = CryptoJS.MD5;
        CryptoJS.MD5 = function(message) {
            const result = originalMD5(message);
            console.log('[Crypto Hook] MD5 input:', message.toString());
            console.log('[Crypto Hook] MD5 output:', result.toString());
            console.trace();
            return result;
        };
    }
})();
```

### Debug Hook
使用 `hooks/debug-hook.js` 设置条件断点：
```javascript
// 在签名函数处设置断点
(function() {
    // 自动搜索sign相关函数
    const scripts = document.getElementsByTagName('script');
    for (let script of scripts) {
        if (script.textContent.includes('sign')) {
            console.log('[Debug] Found sign in script:', script.src || 'inline');
        }
    }
})();
```

## JS搜索工具使用

### 关键词搜索
在项目工作目录内使用 `scripts/js-search-tool.py` 批量搜索JS文件：
```bash
cd reverse-projects/{site_name}
python scripts/js-search-tool.py --js-dir "./capture-data/js/" --keywords "encrypt,sign,md5,sha,crypto" --output "./analysis/search-results/crypto-keywords.json"
```

### 函数提取
搜索并提取完整函数定义：
```bash
python scripts/js-search-tool.py --js-dir "./capture-data/js/" --extract-functions --function-names "getSign,encryptData,calcSignature" --output "./analysis/search-results/functions.json"
```

### Webpack模块分析
分析Webpack打包结构：
```bash
python scripts/js-search-tool.py --js-dir "./capture-data/js/" --analyze-webpack --output "./analysis/search-results/webpack-modules.json"
```

## 输出物规范

### 1. 分析报告 (analysis-report.md)
必须包含以下章节：
- **项目概述**: URL、站点名称、分析时间
- **页面类型判定**: 判定结果、判定依据、置信度
- **抓包数据统计**: 请求数量、API列表、JS文件列表
- **加密参数分析**: 加密参数列表、加密特征、参数生成逻辑
- **逆向过程记录**: 定位方法、分析步骤、遇到的问题
- **最终结论**: 加密算法、签名逻辑、密钥/secret获取方式

### 2. SDK文档 (sdk-document.md)
必须包含：
- **接口列表**: 所有可调用的API接口
- **参数说明**: 每个接口的请求参数
- **返回格式**: 响应数据结构
- **签名算法**: 签名生成逻辑说明
- **使用示例**: 各语言的调用示例
- **错误处理**: 错误码和异常处理

### 3. README.md
必须包含：
- **项目介绍**: SDK用途和功能
- **快速开始**: 安装和基本使用
- **配置说明**: 必需的配置项
- **API参考**: 接口调用方法
- **常见问题**: FAQ
- **更新日志**: 版本变更记录

### 4. SDK代码
必须包含：
- 完整的客户端类
- 签名生成函数
- 加密函数实现
- 错误处理和重试机制
- 单元测试代码
- 使用示例代码

## 验证流程

### SDK验证脚本
在项目工作目录内使用 `scripts/sdk-validator.py` 执行验证：
```bash
cd reverse-projects/{site_name}
python scripts/sdk-validator.py --sdk-path "./output/sdk/python/" --test-url "{原始URL}"
```

### 验证检查项
1. **签名验证**: 生成的签名与抓包签名对比
2. **接口连通性**: 实际调用API验证响应
3. **参数完整性**: 所有必需参数是否正确生成
4. **错误处理**: 异常场景是否正确处理

### 验证结果格式
```json
{
    "timestamp": "2026-04-03T16:00:00",
    "sdk_path": "output/sdk/python/",
    "test_results": {
        "signature_valid": true,
        "api_connectivity": true,
        "param_complete": true,
        "error_handling": true
    },
    "details": {
        "signature_match_rate": "100%",
        "api_success_rate": "95%",
        "tested_endpoints": ["api/data", "api/list"]
    },
    "conclusion": "SDK验证通过，可用于生产环境"
}
```

## 使用示例

### 示例1：完整逆向流程
```
用户: /analyze-url https://api.example.com/v2/data?id=123&sign=abc123

Skill执行:
[Phase 0] 初始化工作目录并复制脚本到 reverse-projects/example-api/scripts/
[Phase 0] 创建项目配置文件: project-config.json
[Phase 1] 页面类型: dynamic (置信度: 85%)
[Phase 2B] DrissionPage抓包完成，保存30个XHR请求
[Phase 2B] JS搜索完成，发现3个包含sign关键词的文件
[Phase 3] 加密参数检测: sign (MD5特征)
[Phase 3] Hook注入分析，定位加密函数在 chunk_456.js
[Phase 3] 逆向成功: sign = MD5(id + timestamp + secret_key)
[Phase 4] SDK验证通过
[Phase 4] 输出完成:
  - output/analysis-report.md
  - output/sdk-document.md
  - output/README.md
  - output/sdk/python/example_api_sdk.py
```

### 示例2：手动执行流程
```bash
# 1. 初始化项目（自动复制scripts和hooks）
python .claude/skills/url-analyzer-sdk-gen/scripts/init-workspace.py --url "https://api.example.com"

# 2. 进入项目目录
cd reverse-projects/example-api

# 3. 使用项目内脚本执行各步骤
python scripts/page-type-detector.py "https://api.example.com"
python scripts/drissionpage-capture.py --url "https://api.example.com" --output "./capture-data"
python scripts/crypto-param-detector.py capture-data/xhr/api-requests.json
python scripts/js-search-tool.py --js-dir "./capture-data/js/"
```

## Hook脚本详解

### 综合Hook脚本 (推荐)
使用 `hooks/all-in-one-hook.js` 一次性注入所有常用Hook：

```javascript
// 包含的Hook功能：
1. Hook Cookie          - 拦截Cookie设置
2. Hook Request Header  - 拦截请求头设置
3. Hook 无限Debugger    - 绕过无限debugger
4. Hook XHR             - 拦截XHR请求
5. Hook Fetch           - 拦截Fetch请求
6. Hook JSON            - 拦截JSON序列化/反序列化
7. Hook Function        - 拦截函数创建
8. Hook WebSocket       - 拦截WebSocket通信
9. Hook String方法       - 拦截字符串操作
10. Hook eval           - 拦截eval执行
11. Hook 定时器         - 拦截setTimeout/setInterval
12. Hook Canvas         - 拦截Canvas创建
13. Hook 加密库         - 拦截CryptoJS/Base64
14. Hook onbeforeunload - 阻止页面跳转
15. 固定随机变量         - 固定时间戳和随机数
```

**使用命令**：
```javascript
// 注入后可用命令
__hook_export__()           // 导出拦截数据
__hook_clear__()            // 清空拦截数据
__hook_set_debug__(bool)    // 开关debugger
__fix_random__(timestamp)   // 固定随机变量
__clear_timers__()          // 清除所有定时器
```

### 单独Hook脚本
| 脚本 | 功能 |
|------|------|
| `hooks/xhr-hook.js` | 仅拦截XHR请求 |
| `hooks/fetch-hook.js` | 仅拦截Fetch请求 |
| `hooks/crypto-hook.js` | 仅拦截加密函数 |
| `hooks/debug-hook.js` | 调试断点工具 |

### Hook注入方式

#### 方式1：浏览器控制台
```javascript
// 1. 打开目标网站
// 2. F12打开DevTools
// 3. Console粘贴Hook脚本执行
```

#### 方式2：Playwright注入
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    # 注入Hook脚本
    with open('hooks/all-in-one-hook.js', 'r') as f:
        page.add_init_script(f.read())
    
    page.goto('https://example.com')
    
    # 获取拦截数据
    data = page.evaluate('window.__hook_export__()')
```

#### 方式3：油猴插件
```javascript
// ==UserScript==
// @name         URL Analyzer Hook
// @match        https://*/*
// @grant        none
// ==/UserScript==

// 粘贴all-in-one-hook.js内容
```

## 技术栈依赖

### Python依赖
安装命令：
```bash
pip install -r requirements.txt
```

核心库说明：

| 类别 | 库 | 用途 |
|------|-----|------|
| 网络请求 | requests | 基础HTTP请求 |
| 网络请求 | curl_cffi | TLS指纹模拟 |
| 网络请求 | aiohttp | 异步HTTP |
| 数据解析 | lxml | XPath提取 |
| 数据解析 | beautifulsoup4 | HTML解析 |
| 自动化 | playwright | 浏览器自动化(推荐) |
| 自动化 | DrissionPage | 轻量级自动化 |
| 加密 | pycryptodome | 标准密码库 |
| 加密 | pyexecjs2 | 调用JS代码 |
| 验证码 | ddddocr | OCR识别 |
| 工具 | loguru | 日志工具 |
| 工具 | tqdm | 进度条 |

### Node.js依赖
安装命令：
```bash
npm install
```

核心库说明：

| 库 | 用途 |
|-----|------|
| playwright | 浏览器自动化 |
| crypto-js | JavaScript加密库 |
| jsdom | DOM模拟 |
| tough-cookie | Cookie处理 |
| axios | HTTP请求 |
| cheerio | HTML解析 |

## 快速开始

### 1. 环境准备
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖（可选，仅使用Playwright时需要）
npm install

# 安装Playwright浏览器（可选，仅使用Playwright时需要）
npx playwright install chromium
```

### 2. 初始化逆向项目
```bash
# 初始化工作目录（会自动复制scripts和hooks到项目目录）
python .claude/skills/url-analyzer-sdk-gen/scripts/init-workspace.py --url "https://api.example.com"

# 进入项目目录
cd reverse-projects/example-api
```

### 3. 执行逆向分析（在项目目录内）
```bash
# 检测页面类型
python scripts/page-type-detector.py "https://api.example.com"

# 使用DrissionPage抓包（推荐）
python scripts/drissionpage-capture.py --url "https://api.example.com" --output "./capture-data"

# 或使用Playwright抓包
node scripts/playwright-capture.js "https://api.example.com" "./capture-data"

# 搜索JS关键词
python scripts/js-search-tool.py --js-dir "./capture-data/js/"

# 验证SDK
python scripts/sdk-validator.py --sdk-path "./output/sdk/python/"
```

### 3. 抓包工具对比

| 特性 | DrissionPage | Playwright |
|------|--------------|------------|
| 资源占用 | 低 | 中 |
| 安装复杂度 | 简单 | 需下载浏览器 |
| 用户数据继承 | 自动继承Chrome | 可配置 |
| 多浏览器支持 | Chrome/Edge | Chromium/Chrome/Edge/Firefox |
| 适用场景 | 大多数逆向场景 | 跨浏览器测试 |

## 相关资源

### Skill源目录（用于初始化）
- **初始化脚本**: `.claude/skills/url-analyzer-sdk-gen/scripts/init-workspace.py`
- **脚本模板**: `.claude/skills/url-analyzer-sdk-gen/scripts/`
- **Hook模板**: `.claude/skills/url-analyzer-sdk-gen/hooks/`
- **输出模板**: `.claude/skills/url-analyzer-sdk-gen/assets/`

### 项目工作目录（初始化后复制）
初始化后，以下资源会被复制到 `reverse-projects/{site_name}/` 目录：
- **scripts/** - 所有分析脚本（可直接执行）
  - `drissionpage-capture.py` - DrissionPage抓包
  - `playwright-capture.js` - Playwright抓包
  - `page-type-detector.py` - 页面类型检测
  - `crypto-param-detector.py` - 加密参数检测
  - `js-search-tool.py` - JS关键词搜索
  - `sdk-validator.py` - SDK验证
- **hooks/** - Hook脚本
  - `all-in-one-hook.js` - 综合Hook
  - `xhr-hook.js`, `fetch-hook.js`, `crypto-hook.js`, `debug-hook.js`

### 参考文档
- **SDK最佳实践**: `references/sdk-best-practices.md`
- **逆向指南**: `references/crypto-reverse-guide.md`
- **依赖配置**: `requirements.txt`, `package.json`