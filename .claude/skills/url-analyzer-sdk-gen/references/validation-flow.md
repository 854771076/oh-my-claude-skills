# 验证流程

## SDK验证脚本

在项目工作目录内使用 `scripts/sdk-validator.py` 执行验证：

```bash
cd reverse-projects/{site_name}

python scripts/sdk-validator.py \
    --sdk-path "./output/sdk/python/" \
    --test-url "{原始URL}"
```

## 验证检查项

1. **签名验证**: 生成的签名与抓包签名对比
2. **接口连通性**: 实际调用API验证响应
3. **参数完整性**: 所有必需参数是否正确生成
4. **错误处理**: 异常场景是否正确处理

## 验证结果格式

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

## 输出位置

验证结果保存到：

- `validation/test-results.json` - 测试结果JSON
- `validation/verify-log.md` - 验证日志

## 验证失败处理

当验证失败时：

1. 检查签名生成逻辑是否正确
2. 检查参数拼接顺序是否与抓包一致
3. 检查密钥/secret是否正确获取
4. 使用Hook注入再次验证加密函数