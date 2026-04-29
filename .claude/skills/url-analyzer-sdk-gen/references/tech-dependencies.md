# 技术栈依赖

## Python依赖

安装命令：

```bash
pip install -r requirements.txt
```

核心库说明：

| 类别     | 库             | 用途               |
| -------- | -------------- | ------------------ |
| **网络请求** | **curl_cffi** | ⭐ **默认推荐** - 模拟浏览器TLS指纹，绕过WAF |
| 网络请求 | requests       | 基础HTTP请求（仅备用，容易被拦截） |
| 网络请求 | aiohttp        | 异步HTTP           |
| 数据解析 | lxml           | XPath提取          |
| 数据解析 | beautifulsoup4 | HTML解析           |
| 自动化   | playwright     | 浏览器自动化(推荐) |
| 自动化   | DrissionPage   | 轻量级自动化       |
| 加密     | pycryptodome   | 标准密码库         |
| 加密     | pyexecjs2      | 调用JS代码         |
| 验证码   | ddddocr        | OCR识别            |
| 工具     | loguru         | 日志工具           |
| 工具     | tqdm           | 进度条             |

## Node.js依赖

安装命令：

```bash
npm install
```

核心库说明：

| 库           | 用途             |
| ------------ | ---------------- |
| playwright   | 浏览器自动化     |
| crypto-js    | JavaScript加密库 |
| jsdom        | DOM模拟          |
| tough-cookie | Cookie处理       |
| axios        | HTTP请求         |
| cheerio      | HTML解析         |

## 环境准备

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖（可选，仅使用Playwright时需要）
npm install

# 安装Playwright浏览器（可选，仅使用Playwright时需要）
npx playwright install chromium
```