# 快速开始指南

## 1. 环境准备

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖（可选，仅使用Playwright时需要）
npm install

# 安装Playwright浏览器（可选）
npx playwright install chromium
```

## 2. 初始化逆向项目

```bash
# 初始化工作目录（会自动复制scripts和hooks到项目目录）
python .claude/skills/url-analyzer-sdk-gen/scripts/init-workspace.py \
    --url "https://api.example.com"

# 进入项目目录
cd reverse-projects/example-api
```

## 3. 首轮分析流程

```bash
# 0. 先做环境检测
python scripts/check-environment.py --json

# 1. 检测页面类型
python scripts/page-type-detector.py "https://api.example.com"

# 2. 使用DrissionPage抓包（推荐）
python scripts/drissionpage-capture.py \
    --url "https://api.example.com" \
    --output "./capture-data"

# 或使用Playwright抓包
node scripts/playwright-capture.js "https://api.example.com" "./capture-data"

# 3. 检测加密参数
python scripts/crypto-param-detector.py capture-data/xhr/api-requests.json

# 4. 搜索JS关键词
python scripts/js-search-tool.py \
    --js-dir "./capture-data/js/" \
    --keywords "encrypt,sign,md5,sha,portal-sign"

# 5. Webpack模块提取（先定位签名模块，再追踪依赖模块）
python scripts/webpack-module-extractor.py capture-data/js/app.js --find-sign-func
python scripts/webpack-module-extractor.py capture-data/js/app.js --extract-module b775
python scripts/webpack-module-extractor.py capture-data/js/app.js --extract-module a078

# 6. Hook注入调试（存在加密参数时）
python scripts/hook-inject-drissionpage.py \
    --url "https://api.example.com" \
    --hook "all-in-one-hook.js" \
    --output "./hook-output" \
    --wait 30

# 7. 验证SDK（生成后必须调用真实接口）
python scripts/sdk-validator.py --sdk-path "./output/sdk/python/" --test-url "https://api.example.com"
```

## 4. 逆向关键经验

- **不要想当然套用标准签名格式**：很多站点并不是 `key=value&key2=value2`，必须从 JS 源码中确认真实拼接方式。
- **默认优先使用 curl_cffi**：真实接口验证时需要浏览器级 TLS 指纹模拟，否则容易被 WAF 403。
- **Key 模块常常藏在依赖里**：签名函数所在模块只负责调用，真实 key / iv / salt 常在 `n("moduleId")` 依赖模块中。
- **必须做三层验证**：签名匹配、真实 API 成功、解密结果正确，缺一不可。

## 5. 输出物位置

逆向完成后，输出物位于：

- `output/analysis-report.md` - 逆向分析报告
- `output/sdk-document.md` - SDK接口说明
- `output/README.md` - 使用说明
- `output/sdk/python/` - Python SDK代码
- `validation/test-results.json` - 自动化验证结果
- `validation/verify-log.md` - 验证日志

## 抓包工具对比

| 特性         | DrissionPage   | Playwright                   |
| ------------ | -------------- | ---------------------------- |
| 资源占用     | 低             | 中                           |
| 安装复杂度   | 简单           | 需下载浏览器                 |
| 用户数据继承 | 自动继承Chrome | 可配置                       |
| 多浏览器支持 | Chrome/Edge    | Chromium/Chrome/Edge/Firefox |
| 适用场景     | 大多数逆向场景 | 跨浏览器测试                 |

## 相关资源

### Skill源目录（用于初始化）

- **初始化脚本**: `.claude/skills/url-analyzer-sdk-gen/scripts/init-workspace.py`
- **脚本模板**: `.claude/skills/url-analyzer-sdk-gen/scripts/`
- **Hook模板**: `.claude/skills/url-analyzer-sdk-gen/hooks/`
- **输出模板**: `.claude/skills/url-analyzer-sdk-gen/assets/`

### 项目工作目录（初始化后复制）

初始化后，以下资源会被复制到 `reverse-projects/{site_name}/` 目录：

- **scripts/** - 所有分析脚本（可直接执行）
- **hooks/** - Hook脚本
- **hook-output/** - Hook调试输出目录
- **validation/** - 真实验证结果目录
- **browser-data/** - 浏览器数据目录（可选）
