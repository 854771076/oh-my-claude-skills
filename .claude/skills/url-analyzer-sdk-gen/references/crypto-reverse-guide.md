# JavaScript加密逆向分析指南

## 概述
本文档提供JavaScript加密函数逆向分析的系统性方法，帮助定位和分析网页中的加密逻辑。

## 逆向分析流程

### Phase 1: 定位加密代码

#### 1.1 关键词搜索
在抓取的JS文件中搜索以下关键词：

```javascript
// 加密函数关键词
const ENCRYPT_KEYWORDS = [
    'encrypt', 'decrypt', 'cipher', 'crypto',
    'sign', 'signature', 'hash', 'digest',
    'md5', 'sha1', 'sha256', 'sha512',
    'aes', 'rsa', 'base64', 'hmac',
    'btoa', 'atob', 'encode', 'decode',
    'CryptoJS', 'crypto-js', 'JSEncrypt'
];

// 签名相关关键词
const SIGN_KEYWORDS = [
    'timestamp', 'nonce', 'random',
    'secret', 'key', 'token', 'auth',
    'getSign', 'makeSign', 'calcSign',
    'generateSignature', 'createSign'
];
```

#### 1.2 Webpack模块分析
定位Webpack打包的加密模块：

```javascript
// Webpack入口点特征
window.webpackJsonp
__webpack_require__
webpack_modules

// 模块搜索方法
function findWebpackModule(keywords) {
    // 遍历所有模块，查找包含关键词的模块
    for (let moduleId in __webpack_modules__) {
        let moduleCode = __webpack_modules__[moduleId].toString();
        if (keywords.some(k => moduleCode.includes(k))) {
            console.log(`模块 ${moduleId} 包含加密逻辑`);
        }
    }
}
```

#### 1.3 浏览器DevTools调试
使用Chrome DevTools定位：

**方法A：XHR断点**
1. 打开DevTools → Sources → XHR/fetch breakpoints
2. 添加包含加密参数的API URL
3. 触发请求，在断点处查看调用栈
4. 沿调用栈找到加密函数位置

**方法B：事件监听断点**
1. Sources → Event Listener Breakpoints
2. 选择XHR → send
3. 触发请求，跟踪调用链

**方法C：覆盖函数**
```javascript
// 覆盖原生函数来拦截调用
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('Fetch调用:', args);
    console.trace(); // 打印调用栈
    return originalFetch.apply(this, args);
};

// 覆盖XMLHttpRequest
const originalOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
    console.log('XHR open:', method, url);
    console.trace();
    return originalOpen.apply(this, arguments);
};
```

### Phase 2: 分析加密算法

#### 2.1 常见加密算法识别

**MD5特征**：
- 输出长度：32字符（十六进制）
- 函数特征：`CryptoJS.MD5()`, `md5()`, `hex_md5()`

**SHA特征**：
- SHA1: 40字符
- SHA256: 64字符
- SHA512: 128字符
- 函数特征：`CryptoJS.SHA1()`, `CryptoJS.SHA256()`

**Base64特征**：
- 输出包含`+`, `/`, `=`
- 函数特征：`btoa()`, `Base64.encode()`

**AES特征**：
- 输出通常是Base64编码的密文
- 需要密钥和IV
- 函数特征：`CryptoJS.AES.encrypt()`

#### 2.2 签名逻辑分析

**常见签名模式**：

1. **时间戳签名**：
```javascript
// 常见模式：sign = MD5(params + timestamp + key)
function getSign(params, timestamp, key) {
    let sortedParams = Object.keys(params)
        .sort()
        .map(k => `${k}=${params[k]}`)
        .join('&');
    return md5(sortedParams + timestamp + key);
}
```

2. **HMAC签名**：
```javascript
// HMAC-SHA256
function hmacSign(data, key) {
    return CryptoJS.HmacSHA256(data, key).toString();
}
```

3. **多次哈希**：
```javascript
// 二次哈希增强安全性
function doubleHash(data) {
    let first = md5(data);
    return sha256(first);
}
```

4. **参数拼接签名**：
```javascript
// 参数名+值拼接
function concatSign(params, secret) {
    let str = Object.keys(params)
        .sort()
        .map(k => `${k}${params[k]}`)
        .join('');
    return md5(str + secret);
}
```

### Phase 3: 提取加密函数

#### 3.1 直接提取
当加密函数未被混淆时：

```javascript
// 找到清晰的加密函数
function encrypt(params) {
    const timestamp = Date.now();
    const nonce = Math.random().toString(36).substr(2);
    const str = JSON.stringify(params) + timestamp + nonce + SECRET_KEY;
    return {
        sign: CryptoJS.MD5(str).toString(),
        timestamp: timestamp,
        nonce: nonce
    };
}

// 直接复制该函数到SDK中
```

#### 3.2 混淆代码还原
当代码被混淆时：

**常见混淆模式**：
```javascript
// 混淆示例
var _0x1234 = ['md5', 'sha256', 'timestamp'];
function _0xabcd(_0xa, _0xb) {
    return _0x1234[0](_0xa + _0xb);
}

// 还原方法
// 1. 使用在线反混淆工具
// 2. 手动替换变量名
// 3. 运行测试验证结果
```

**反混淆工具**：
- https://www.danstools.com/javascript-beautify/
- https://lelinhtinh.github.io/de4js/
- Chrome DevTools的Pretty Print功能

#### 3.3 动态提取
使用浏览器环境执行并捕获：

```javascript
// 在页面控制台执行
(function() {
    // 保存原始函数引用
    const original = window.getSign;

    // 覆盖函数，记录参数和结果
    window.getSign = function(...args) {
        console.log('=== 签名函数调用 ===');
        console.log('输入参数:', args);
        const result = original.apply(this, args);
        console.log('输出结果:', result);
        console.log('调用栈:', new Error().stack);
        return result;
    };
})();

// 触发API调用，查看记录的签名函数行为
```

### Phase 4: 验证和复现

#### 4.1 验证签名逻辑
```python
import hashlib
import json

def verify_sign(params, timestamp, secret_key):
    """验证提取的签名逻辑"""
    # 按文档中的逻辑实现
    sorted_params = sorted(params.items())
    param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_text = f"{param_str}{timestamp}{secret_key}"
    calculated_sign = hashlib.md5(sign_text.encode()).hexdigest()

    # 与抓包获取的签名对比
    captured_sign = "abc123..."  # 从抓包数据获取

    if calculated_sign == captured_sign:
        print("签名逻辑验证成功!")
        return True
    else:
        print(f"验证失败: 计算={calculated_sign}, 抓包={captured_sign}")
        return False
```

#### 4.2 多次测试验证
```python
# 使用多组数据验证
test_cases = [
    {'params': {'id': 1}, 'timestamp': 1234567890, 'expected': 'sign1'},
    {'params': {'id': 2, 'name': 'test'}, 'timestamp': 1234567891, 'expected': 'sign2'},
]

for case in test_cases:
    result = verify_sign(case['params'], case['timestamp'], SECRET_KEY)
    assert result['sign'] == case['expected'], f"测试失败: {case}"
```

### Phase 5: SDK实现

#### 5.1 完整实现示例
```python
class SignSDK:
    """签名SDK实现"""

    SECRET_KEY = "提取的密钥"

    def generate_sign(self, params: dict) -> dict:
        """生成签名参数"""
        timestamp = int(time.time())
        nonce = self._generate_nonce()

        # 实现提取的签名逻辑
        sorted_params = sorted(params.items())
        param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_text = f"{param_str}{timestamp}{nonce}{self.SECRET_KEY}"
        sign = hashlib.md5(sign_text.encode()).hexdigest()

        return {
            **params,
            'sign': sign,
            'timestamp': timestamp,
            'nonce': nonce
        }
```

## 常见加密库识别

### CryptoJS
```javascript
// 特征代码
CryptoJS.MD5(message)
CryptoJS.SHA256(message)
CryptoJS.AES.encrypt(message, key)
CryptoJS.HmacSHA256(message, key)

// 引入方式
<script src="crypto-js.js"></script>
// 或
import CryptoJS from 'crypto-js';
```

### JSEncrypt (RSA)
```javascript
// 特征代码
const encrypt = new JSEncrypt();
encrypt.setPublicKey(publicKey);
const encrypted = encrypt.encrypt(data);
```

### Node-forge
```javascript
// 特征代码
forge.md.md5.create().update(data).digest().toHex();
forge.util.encode64(data);
```

## 人工介入指引

当自动逆向失败时，建议用户：

1. **提供加密函数代码片段**
   ```
   请在浏览器DevTools中找到以下内容并提供：
   - 包含sign/encrypt关键词的函数完整代码
   - 函数的调用位置和参数
   ```

2. **描述加密逻辑**
   ```
   如果无法直接复制代码，请描述：
   - 参数是如何拼接的？（key=value? key+value?）
   - 使用了哪些哈希函数？（MD5? SHA256? 多次哈希?）
   - 是否有时间戳或随机字符串参与？
   ```

3. **提供调试信息**
   ```
   请提供以下调试信息：
   - 函数输入参数的具体值
   - 函数输出的具体签名值
   - 多次调用的参数和结果对比（用于分析动态部分）
   ```

## Hook技术详解

### 什么是Hook
Hook（钩子）是一种拦截函数调用的技术，可以在不修改原始代码的情况下，监控或修改函数的行为。在逆向分析中，Hook是定位加密函数的利器。

### Hook脚本使用方式
本skill提供了多个Hook脚本，存放在 `hooks/` 目录：

1. **xhr-hook.js** - 拦截XMLHttpRequest请求
2. **fetch-hook.js** - 拦截Fetch请求
3. **crypto-hook.js** - 拦截加密函数调用
4. **debug-hook.js** - 调试辅助工具

### 注入Hook的方式

#### 方式1：浏览器控制台直接注入
```javascript
// 1. 打开目标网站
// 2. 按F12打开DevTools
// 3. 切换到Console标签
// 4. 复制Hook脚本内容粘贴执行
```

#### 方式2：Playwright自动注入
```javascript
const { chromium } = require('playwright');
const fs = require('fs');

// 读取Hook脚本
const hookScript = fs.readFileSync('hooks/crypto-hook.js', 'utf8');

const browser = await chromium.launch();
const page = await browser.newPage();

// 注入Hook
await page.addInitScript(hookScript);

// 访问目标页面
await page.goto('https://example.com');

// 获取拦截数据
const cryptoData = await page.evaluate(() => window.__crypto_intercept_data__);
console.log(cryptoData);
```

#### 方式3：Tampermonkey/油猴插件
```javascript
// ==UserScript==
// @name         Crypto Hook
// @match        https://example.com/*
// @grant        none
// ==/UserScript==

// 将Hook脚本内容粘贴到这里
```

### XHR Hook详解
拦截所有XMLHttpRequest请求，记录：
- 请求URL、方法、参数
- 响应数据
- 完整调用栈

```javascript
// 注入xhr-hook.js后可用命令
__export_xhr_data__()   // 导出拦截数据
__clear_xhr_data__()    // 清空数据
```

**典型输出**：
```javascript
{
    method: 'POST',
    url: 'https://api.example.com/data',
    headers: { 'Content-Type': 'application/json' },
    postData: '{"id":123,"sign":"abc123"}',
    responseText: '{"code":0,"data":{...}}',
    callStack: 'Error: Stack trace\n    at XMLHttpRequest.send...'
}
```

### Crypto Hook详解
自动拦截常见加密库的调用：

**支持的加密库**：
- CryptoJS (MD5, SHA系列, AES, HmacSHA256等)
- 原生Base64 (btoa/atob)
- encodeURIComponent

**使用示例**：
```javascript
// 注入crypto-hook.js后
// 触发API调用，加密函数会被自动拦截

// 查看拦截数据
__export_crypto_data__()

// 输出示例
[
    {
        type: 'CryptoJS.MD5',
        input: 'id=123&timestamp=1712134567secret_key',
        output: 'abc123def456...',
        timestamp: 1712134567890
    }
]

// 搜索页面中的加密函数
__find_crypto_functions__()
```

### Debug Hook详解
提供强大的调试功能：

```javascript
// 设置函数断点 - 当函数被调用时自动暂停
__set_breakpoint__('getSign')

// 设置条件断点 - 仅当条件满足时暂停
__set_conditional_breakpoint__('encrypt', (data) => data.length > 100)

// 监控变量变化 - 变量被修改时自动暂停
__watch_var__('SECRET_KEY')

// 搜索函数定义
__search_function__('getSign')

// 自动设置加密函数断点
__auto_break_crypto__()

// 追踪对象的所有方法
__trace_object__(window.api, 'api')
```

## 高级逆向技巧

### 1. Webpack模块查找
```javascript
// 查找Webpack入口
if (window.webpackJsonp) {
    // 遍历所有chunk
    window.webpackJsonp.forEach((chunk, idx) => {
        console.log(`Chunk ${idx}:`, chunk);
    });
}

// 查找特定模块
function findModuleByExport(exportName) {
    if (typeof __webpack_require__ !== 'undefined') {
        for (let id in __webpack_modules__) {
            try {
                let module = __webpack_require__(id);
                if (module && module[exportName]) {
                    console.log(`Found ${exportName} in module ${id}`);
                }
            } catch(e) {}
        }
    }
}
```

### 2. 原型链Hook
```javascript
// Hook Array.prototype.join (常用于参数拼接)
const originalJoin = Array.prototype.join;
Array.prototype.join = function(separator) {
    const result = originalJoin.apply(this, arguments);
    if (this.length > 3 && result.length > 50) {
        console.log('[Hook] Array.join:', result.substring(0, 100));
        console.trace();
    }
    return result;
};
```

### 3. JSON.stringify Hook
```javascript
// 很多签名会对JSON字符串做处理
const originalStringify = JSON.stringify;
JSON.stringify = function(obj) {
    const result = originalStringify.apply(this, arguments);
    if (result && result.length > 20) {
        console.log('[Hook] JSON.stringify:', result.substring(0, 200));
        console.trace();
    }
    return result;
};
```

### 4. 时间戳分析
```javascript
// 记录所有时间戳生成
const originalDateNow = Date.now;
Date.now = function() {
    const timestamp = originalDateNow.apply(this, arguments);
    console.log('[Hook] Date.now():', timestamp);
    return timestamp;
};

const originalGetTime = Date.prototype.getTime;
Date.prototype.getTime = function() {
    const timestamp = originalGetTime.apply(this, arguments);
    console.log('[Hook] getTime():', timestamp);
    return timestamp;
};
```

### 5. Object.defineProperty监控
```javascript
// 监控对象属性被设置
function watchProperty(obj, propName) {
    let value = obj[propName];

    Object.defineProperty(obj, propName, {
        get: function() {
            console.log(`[Watch] Getting ${propName}`);
            return value;
        },
        set: function(newValue) {
            console.log(`[Watch] Setting ${propName} =`, newValue);
            console.trace();
            value = newValue;
        },
        configurable: true
    });
}

// 监控window.sign
watchProperty(window, 'sign');
```

## 逆向案例实战

### 案例1：时间戳+MD5签名
**目标**：分析 `https://api.example.com/data?id=1&sign=abc123`

**步骤**：
1. 注入 `crypto-hook.js`
2. 注入 `xhr-hook.js`
3. 触发API请求
4. 查看拦截数据

```javascript
// Crypto Hook输出
{
    type: 'CryptoJS.MD5',
    input: 'id=1&timestamp=1712134567my_secret_key',
    output: 'abc123def456...'
}

// 分析结论
// sign = MD5('id=' + id + '&timestamp=' + ts + 'my_secret_key')
```

### 案例2：AES加密参数
**目标**：分析请求体中的加密data字段

```javascript
// 注入crypto-hook.js后触发请求
{
    type: 'CryptoJS.AES.encrypt',
    message: '{"user":"admin","pass":"123456"}',
    key: 'aes_key_12345',
    result: 'U2FsdGVkX1...'
}

// 密钥已暴露，可在SDK中实现
```

### 案例3：动态密钥获取
**目标**：密钥从服务器动态获取

```javascript
// 使用XHR Hook查看密钥请求
{
    url: 'https://api.example.com/getKey',
    responseText: '{"key":"dynamic_key_xxx"}'
}

// 在签名函数调用时，key值来自之前的请求
```

## 总结

逆向分析的核心步骤：
1. 定位：关键词搜索 + Webpack分析 + DevTools调试
2. Hook注入：XHR Hook + Crypto Hook + Debug Hook
3. 分析：识别加密算法 + 分析签名逻辑
4. 提取：直接复制 + 反混淆 + 动态捕获
5. 验证：多组数据测试确保逻辑正确
6. 实现：在SDK中复现加密函数

**推荐工作流**：
```
1. init-workspace.py → 创建工作目录
2. playwright-capture.js → 抓包获取基础数据
3. crypto-hook.js → 注入Hook获取加密细节
4. js-search-tool.py → 搜索JS代码
5. sdk-validator.py → 验证SDK正确性
```