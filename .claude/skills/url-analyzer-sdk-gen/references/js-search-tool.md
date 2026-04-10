# JS搜索工具使用

## 关键词搜索

在项目工作目录内使用 `scripts/js-search-tool.py` 批量搜索JS文件：

```bash
cd reverse-projects/{site_name}

# 基础关键词搜索
python scripts/js-search-tool.py \
    --js-dir "./capture-data/js/" \
    --keywords "encrypt,sign,md5,sha,crypto" \
    --output "./analysis/search-results/crypto-keywords.json"
```

## 函数提取

搜索并提取完整函数定义：

```bash
python scripts/js-search-tool.py \
    --js-dir "./capture-data/js/" \
    --extract-functions \
    --function-names "getSign,encryptData,calcSignature" \
    --output "./analysis/search-results/functions.json"
```

## Webpack模块分析

分析Webpack打包结构：

```bash
python scripts/js-search-tool.py \
    --js-dir "./capture-data/js/" \
    --analyze-webpack \
    --output "./analysis/search-results/webpack-modules.json"
```

## 搜索关键词列表

**加密函数关键词**：

```javascript
const ENCRYPT_KEYWORDS = [
    'encrypt', 'decrypt', 'cipher', 'crypto',
    'sign', 'signature', 'hash', 'digest',
    'md5', 'sha1', 'sha256', 'sha512',
    'aes', 'rsa', 'base64', 'hmac',
    'btoa', 'atob', 'encode', 'decode',
    'CryptoJS', 'crypto-js', 'JSEncrypt'
];
```

**签名相关关键词**：

```javascript
const SIGN_KEYWORDS = [
    'timestamp', 'nonce', 'random',
    'secret', 'key', 'token', 'auth',
    'getSign', 'makeSign', 'calcSign',
    'generateSignature', 'createSign'
];
```

## 输出结果

搜索结果保存到 `analysis/search-results/` 目录：

```
analysis/search-results/
├── crypto-keywords.json    # 加密关键词搜索结果
├── sign-functions.json     # 签名函数搜索结果
├── functions.json          # 提取的完整函数
└── webpack-modules.json    # Webpack模块分析
```

**结果格式**：

```json
{
  "search_time": "2026-04-09T10:00:00",
  "keywords": ["encrypt", "sign"],
  "results": [
    {
      "file": "chunk_456.js",
      "matches": [
        {
          "keyword": "encrypt",
          "line": 123,
          "context": "function encryptData(data) {...}",
          "function_name": "encryptData"
        }
      ]
    }
  ]
}
```