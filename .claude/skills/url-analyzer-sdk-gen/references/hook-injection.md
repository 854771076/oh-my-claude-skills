# Hook注入调试指南

## Hook脚本列表

| Hook脚本            | 功能描述           | 适用场景                     |
| ------------------- | ------------------ | ---------------------------- |
| `all-in-one-hook.js`| 综合Hook（推荐）   | 包含所有Hook功能，一键启用   |
| `xhr-hook.js`       | XHR请求拦截        | 定位XHR请求的发起位置        |
| `fetch-hook.js`     | Fetch请求拦截      | 定位Fetch请求的发起位置      |
| `crypto-hook.js`    | 加密函数拦截       | 拦截CryptoJS、Base64调用     |
| `debug-hook.js`     | 调试断点工具       | 搜索sign相关函数             |

## 综合Hook功能

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
__hook_export__()           // 导出拦截数据
__hook_clear__()            // 清空拦截数据
__hook_set_debug__(bool)    // 开关debugger
__fix_random__(timestamp)   // 固定随机变量
__clear_timers__()          // 清除所有定时器
```

## DrissionPage Hook注入

```bash
cd reverse-projects/{site_name}

# 列出可用Hook
python scripts/hook-inject-drissionpage.py --list-hooks

# 使用综合Hook（推荐）
python scripts/hook-inject-drissionpage.py \
    --url "{url}" \
    --hook "all-in-one-hook.js" \
    --output "./hook-output" \
    --wait 30 \
    --headed

# 仅调试加密函数
python scripts/hook-inject-drissionpage.py \
    --url "{url}" \
    --hook "crypto-hook.js" \
    --wait 60

# 使用自定义Hook
python scripts/hook-inject-drissionpage.py \
    --url "{url}" \
    --hook-dir "./hooks" \
    --hook "my-custom-hook.js"
```

## Playwright Hook注入

```bash
cd reverse-projects/{site_name}

# 列出可用Hook
python scripts/hook-inject-playwright.py --list-hooks

# 使用init_script注入（推荐）
python scripts/hook-inject-playwright.py \
    --url "{url}" \
    --hook "all-in-one-hook.js" \
    --output "./hook-output" \
    --wait 30 \
    --headed

# 使用持久化上下文保存登录态
python scripts/hook-inject-playwright.py \
    --url "{url}" \
    --hook "crypto-hook.js" \
    --user-data-dir "./browser-data"

# 使用Chrome浏览器
python scripts/hook-inject-playwright.py \
    --url "{url}" \
    --hook "all-in-one-hook.js" \
    --browser chrome
```

## Hook输出分析

输出目录结构：

```
hook-output/
├── intercept/
│   ├── hook-data.json      # 所有拦截数据
│   └── analysis.json       # 分类分析结果
├── console/
│   └── console-logs.json   # Console输出日志
├── network/
│   └── network-logs.json   # 网络请求日志
├── screenshots/
│   └── page.png            # 页面截图
├── page.html               # 页面HTML
└── cookies.json            # Cookies
```

### 关键输出分析

**analysis.json** - 拦截数据分类统计：

```json
{
  "summary": {
    "total_count": 156,
    "types_count": {
      "xhr_open": 45,
      "xhr_send": 45,
      "xhr_response": 40,
      "md5": 3,
      "sha256": 2,
      "btoa": 10
    }
  },
  "crypto_operations": [
    {"type": "md5", "data": {"input": "id=123&ts=123456", "output": "abc..."}}
  ],
  "xhr_requests": [...]
}
```

**加密函数拦截** - 定位加密入口：

```
[Hook] CryptoJS.MD5 => id=123&timestamp=123456&secret=xxx
[Hook] CryptoJS.MD5 output => abc123def456
```

## 定位加密代码

1. **检查Console日志中的调用栈**
   - Hook脚本会打印 `console.trace()` 显示调用栈
   - 确定加密函数被调用的JS文件和行号

2. **结合JS搜索工具**：

```bash
python scripts/js-search-tool.py \
    --js-dir "./capture-data/js/" \
    --keywords "encrypt,sign,md5" \
    --output "./analysis/search-results/"
```

3. **Webpack模块分析**：

```bash
python scripts/js-search-tool.py \
    --js-dir "./capture-data/js/" \
    --analyze-webpack \
    --output "./analysis/search-results/webpack-modules.json"
```

## 人工介入指引

当自动分析无法定位加密逻辑时：

```
【Hook调试结果分析】

1. 拦截到的加密操作:
   - MD5调用: 3次
     输入: "id=123&ts=123456&secret=xxx"
     输出: "abc123def456"
   
2. XHR请求签名:
   - URL: https://api.example.com/api/data
   - 参数: {"id":123,"sign":"abc123"}
   
3. Console调用栈显示加密位置:
   - chunk_456.js:123 (包含 encrypt 关键词)
   
4. 建议下一步操作:
   - 打开DevTools，在chunk_456.js:123设置断点
   - 手动触发请求，观察加密函数执行过程
   - 或提供加密函数的JS代码片段以便分析

Hook脚本已准备好:
  - hooks/crypto-hook.js 可继续注入调试
  - hooks/debug-hook.js 可设置断点搜索
```