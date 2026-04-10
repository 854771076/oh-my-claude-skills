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

## 3. 执行逆向分析

```bash
# 检测页面类型
python scripts/page-type-detector.py "https://api.example.com"

# 使用DrissionPage抓包（推荐）
python scripts/drissionpage-capture.py \
    --url "https://api.example.com" \
    --output "./capture-data"

# 或使用Playwright抓包
node scripts/playwright-capture.js "https://api.example.com" "./capture-data"

# 搜索JS关键词
python scripts/js-search-tool.py --js-dir "./capture-data/js/"

# Hook注入调试（存在加密参数时）
python scripts/hook-inject-drissionpage.py \
    --url "https://api.example.com" \
    --hook "all-in-one-hook.js"

# 验证SDK
python scripts/sdk-validator.py --sdk-path "./output/sdk/python/"
```

## 4. 输出物位置

逆向完成后，输出物位于：

- `output/analysis-report.md` - 逆向分析报告
- `output/sdk-document.md` - SDK接口说明
- `output/README.md` - 使用说明
- `output/sdk/python/` - Python SDK代码

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