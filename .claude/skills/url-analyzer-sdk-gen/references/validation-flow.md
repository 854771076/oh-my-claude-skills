# 验证流程

## ⚠️ 验证核心原则

**没有经过真实API验证的SDK = 不可用**

必须完成 **三层验证** 才能算逆向完成：

| 层级 | 验证内容 | 通过标准 | 重要性 |
|------|---------|---------|-------|
| L1 | 签名算法正确性 | 生成的签名与抓包签名 100% 相同 | 🔴 强制 |
| L2 | 真实接口请求验证 | State=200 或 Success=true | 🔴 强制 |
| L3 | 响应数据解密验证 | 解密后数据结构正确、字段完整 | 🔴 强制 |

---

## 验证执行流程

### Phase 1: 签名算法验证（第一步）

使用捕获的请求参数进行纯算法验证：

```python
import hashlib

# 从抓包中获取的原始数据
captured_params = {
    "key": "value",
    "ts": 1234567890,
    "other": "data"
}
captured_sign = "abc123def456..."  # 从抓包中提取

# 使用SDK生成签名
generated_sign = sdk.generate_sign(captured_params)

# 验证
assert generated_sign == captured_sign, \
    f"签名不匹配!\n期望: {captured_sign}\n实际: {generated_sign}"
```

**签名不匹配时的调试步骤**：
1. 打印排序后的参数列表
2. 打印拼接后的完整字符串
3. 对比JS源码中的拼接逻辑
4. 检查是否需要 `JSON.stringify` 对象/数组
5. 检查空值、特殊字符的处理方式

---

### Phase 2: 真实API请求验证（强制）

在项目工作目录内执行：

```bash
cd reverse-projects/{site_name}

# 使用生成的SDK调用真实API
python -c "
import sys
sys.path.insert(0, './output/sdk/python')
from your_sdk import Client

client = Client()
result = client.request_post('/test/endpoint', {
    'param1': 'value1',
    'ts': your_timestamp
})

# 验证响应状态
assert result.get('State') == '200' or result.get('Success') == True, \\
    f'API请求失败: {result}'
print('✅ L2 真实API验证通过')
print('响应预览:', str(result)[:200])
"
```

**常见失败原因与解决**：

| 错误 | 原因 | 解决方法 |
|------|------|---------|
| 403 Forbidden | TLS指纹被WAF拦截 | 改用 curl_cffi + impersonate |
| portal-sign错误 | 签名算法/参数/时间戳不对 | 回到L1仔细调试签名 |
| 响应Data为空 | 需要特定请求头或cookie | 检查抓包中的所有请求头 |

---

### Phase 3: 响应解密验证

验证AES解密是否正确：

```python
# 从抓包中获取加密的响应数据
encrypted_data = captured_response["Data"]

# 使用SDK解密
decrypted = client.decrypt(encrypted_data)
print("解密结果:", decrypted)

# 验证数据结构
parsed = json.loads(decrypted)
assert isinstance(parsed, (dict, list)), "解密结果不是JSON格式"
```

---

## 自动化验证脚本

```bash
cd reverse-projects/{site_name}

python scripts/sdk-validator.py \
    --sdk-path "./output/sdk/python/" \
    --test-url "{原始URL}"
```

## 验证结果格式

```json
{
    "timestamp": "2026-04-03T16:00:00",
    "sdk_path": "output/sdk/python/",
    "test_results": {
        "signature_valid": true,
        "api_connectivity": true,
        "decryption_valid": true,
        "error_handling": true
    },
    "details": {
        "signature_match": "100%",
        "api_http_status": 200,
        "api_response_state": "200",
        "decrypted_data_sample": "{...}",
        "tested_endpoints": ["/api/data", "/api/list"]
    },
    "conclusion": "✅ 三层验证全部通过，SDK可用于生产"
}
```

## 输出位置

验证结果保存到：

- `validation/test-results.json` - 测试结果JSON
- `validation/verify-log.md` - 验证日志

## 验证失败处理流程

当验证失败时，按此顺序排查：

```
签名不匹配 → 打印中间结果对比
    ↓
├─ 参数排序是否正确？
├─ 拼接分隔符是否正确？
├─ 空值处理是否与JS一致？
├─ 对象/数组是否需要JSON.stringify？
└─ 编码方式是否正确(UTF-8/GBK)？

API请求失败
    ↓
├─ 403 → 改用curl_cffi模拟浏览器TLS
├─ 401 → 检查Cookie/Token是否完整
└─ 签名错误 → 回到L1重新验证签名

解密失败
    ↓
├─ AES Key/IV是否正确提取？
├─ 加密模式是否匹配(CBC/ECB等)
├─ 填充模式是否正确(PKCS7)
└─ Base64解码是否正确(注意填充等号)
```

**关键提示**: 永远不要假设算法逻辑，必须从JS源码中提取并验证。看起来像 `key=value&` 格式，实际可能只是 `keyvalue` 直接拼接。