# 抓包工具使用指南

## 工具对比

| 特性         | DrissionPage   | Playwright                   |
| ------------ | -------------- | ---------------------------- |
| 资源占用     | 低             | 中                           |
| 安装复杂度   | 简单           | 需下载浏览器                 |
| 用户数据继承 | 自动继承Chrome | 可配置                       |
| 多浏览器支持 | Chrome/Edge    | Chromium/Chrome/Edge/Firefox |
| 适用场景     | 大多数逆向场景 | 跨浏览器测试                 |

## DrissionPage (推荐)

**优势**：轻量级、资源占用低、CDP协议、自动继承Chrome用户数据

### 基础用法

```bash
cd reverse-projects/{site_name}

# 基础抓包
python scripts/drissionpage-capture.py --url "{url}" --output "./capture-data"

# 可选参数：
# --headed       有头模式（显示浏览器）
# --browser edge 使用Edge浏览器
# --no-user-data 不继承用户数据
# --verbose      详细日志
```

### 登录态抓包

```bash
# 使用项目目录下的浏览器数据（需先手动登录）
python scripts/drissionpage-capture.py \
    --url "{url}" \
    --output "./capture-data" \
    --user-data-dir "./browser-data"
```

## Playwright

**优势**：支持多浏览器、功能强大、精确的用户数据控制、init_script注入

### 基础用法

```bash
cd reverse-projects/{site_name}

# 基础抓包
node scripts/playwright-capture.js "{url}" "./capture-data"

# 使用持久化上下文
node scripts/playwright-capture.js "{url}" "./capture-data" \
    --user-data-dir "./browser-data"

# 使用Chrome浏览器
node scripts/playwright-capture.js "{url}" "./capture-data" \
    --browser chrome
```

### 浏览器选择

| 浏览器      | 说明                                    |
| ----------- | --------------------------------------- |
| Chromium    | 自动下载，无需本地安装                  |
| Chrome      | 使用本地Chrome，需已安装                |
| Edge        | 使用本地Edge，需已安装                  |
| Firefox     | 使用本地或自动下载的Firefox             |

## 手动登录流程

当目标网站需要登录时：

```bash
# 1. 执行手动登录脚本
python scripts/manual-login.py \
    --url "{url}" \
    --browser {browser} \
    --user-data-dir "./browser-data"

# 2. 用户在浏览器中完成登录操作
# 3. 登录完成后关闭浏览器
# 4. 后续抓包使用同一用户数据目录
python scripts/drissionpage-capture.py \
    --url "{url}" \
    --user-data-dir "./browser-data"
```

## 输出数据

抓包完成后生成：

```
capture-data/
├── har/                    # HAR格式完整抓包
│   └── capture.har
├── xhr/                    # XHR/Fetch请求JSON
│   └── api-requests.json
├── js/                     # JS文件内容
│   └── chunk_123.js
│   └── chunk_456.js
└── headers/                # 请求头分析
    └── headers-summary.json
```