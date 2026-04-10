#!/usr/bin/env python3
"""
输出文档模板生成器
生成逆向分析报告、SDK文档、README

使用方式:
python output-templates-generator.py \
    --workspace "./reverse-projects/example-api" \
    --analysis-data "./analysis/crypto-analysis.json" \
    --sdk-path "./output/sdk/python/"
"""

import os
import json
from datetime import datetime
from pathlib import Path


class OutputTemplateGenerator:
    """输出文档模板生成器"""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载项目配置"""
        config_path = self.workspace / "project-config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def generate_analysis_report(self, analysis_data: dict = None) -> str:
        """
        生成逆向分析报告

        Args:
            analysis_data: 分析数据

        Returns:
            Markdown格式的报告
        """
        url = self.config.get('url_info', {}).get('path', '')
        hostname = self.config.get('url_info', {}).get('hostname', '')

        report = f"""# 逆向分析报告

## 项目概述

| 项目 | 内容 |
|------|------|
| **目标URL** | {self.config.get('project_info', {}).get('url', '')} |
| **站点名称** | {self.config.get('project_info', {}).get('name', '')} |
| **分析时间** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| **状态** | {self.config.get('project_info', {}).get('status', '')} |

## 1. 页面类型判定

### 判定结果
- **页面类型**: `{analysis_data.get('page_type', 'unknown') if analysis_data else 'unknown'}`
- **置信度**: `{analysis_data.get('confidence', 0) if analysis_data else 0}%`
- **判定依据**: {self._format_evidence(analysis_data.get('evidence', []) if analysis_data else [])}

### 建议
{analysis_data.get('recommendation', '无') if analysis_data else '待分析'}

## 2. 网络抓包统计

### 请求概览
- **总请求数**: [从抓包数据获取]
- **XHR/Fetch请求**: [从抓包数据获取]
- **JS文件数量**: [从抓包数据获取]

### 关键API列表
| API端点 | 方法 | 是否加密 |
|---------|------|----------|
| /api/data | GET | 是 (sign) |
| /api/list | POST | 否 |

## 3. 加密参数分析

### 加密参数识别
{self._format_crypto_analysis(analysis_data)}

### 加密特征
- **加密算法**: [从分析获取]
- **参数生成逻辑**: [详细描述]
- **密钥位置**: [JS文件路径]

## 4. 逆向过程记录

### 4.1 定位加密函数
**搜索关键词**: `encrypt`, `sign`, `md5`, `sha`

**定位结果**:
1. `chunk_123.js` - 包含 `sign` 关键词
2. `main.js` - 包含 `md5` 函数调用

### 4.2 分析加密逻辑
**加密函数位置**: `chunk_123.js` 第 456 行

**函数签名**:
```javascript
function getSign(params, timestamp, secretKey) {{
    // ...
}}
```

**算法流程**:
1. 参数按key排序
2. 拼接成字符串
3. 添加时间戳和密钥
4. MD5哈希

### 4.3 提取密钥
**密钥来源**: [固定值/动态生成/从服务器获取]

**密钥值**: `[已提取的密钥]`

## 5. 遇到的问题与解决

### 问题1: [问题描述]
- **现象**:
- **原因**:
- **解决方案**:

## 6. 最终结论

### 加密算法
```
sign = MD5(sorted_params + timestamp + secret_key)
```

### 参数生成规则
| 参数 | 生成方式 | 示例 |
|------|----------|------|
| timestamp | 当前时间戳(秒) | 1712134567 |
| sign | MD5签名 | abc123... |
| nonce | 随机字符串 | x7y8z9 |

### SDK实现状态
- [x] Python SDK
- [x] JavaScript SDK
- [ ] Java SDK

## 附录

### A. 相关文件路径
- 抓包数据: `capture-data/xhr/`
- JS文件: `capture-data/js/`
- 分析结果: `analysis/`
- SDK代码: `output/sdk/`

### B. 参考资料
- [JS加密逆向分析指南](../references/crypto-reverse-guide.md)
- [SDK最佳实践](../references/sdk-best-practices.md)

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return report

    def generate_sdk_document(self, sdk_info: dict = None) -> str:
        """
        生成SDK接口说明文档

        Args:
            sdk_info: SDK信息

        Returns:
            Markdown格式的文档
        """
        doc = f"""# SDK接口说明文档

## 概述
本文档描述了 {self.config.get('project_info', {}).get('name', '')} API的调用方法和签名规则。

## 快速开始

### Python
```python
from {self.config.get('project_info', {}).get('name', 'api')}_sdk import APIClient

client = APIClient()
result = client.get_data(param1='value1')
print(result)
```

### JavaScript
```javascript
const {{ APIClient }} = require('./sdk');

const client = new APIClient();
const result = await client.getData({{ param1: 'value1' }});
console.log(result);
```

## 接口列表

### 1. 获取数据 (GET /api/data)

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | string | 是 | 数据ID |
| page | int | 否 | 页码，默认1 |
| limit | int | 否 | 每页数量，默认20 |

**签名参数** (自动生成):

| 参数名 | 类型 | 说明 |
|--------|------|------|
| timestamp | int | 当前时间戳(秒) |
| sign | string | MD5签名 |
| nonce | string | 随机字符串 |

**响应格式**:
```json
{{
    "code": 0,
    "message": "success",
    "data": {{
        "items": [],
        "total": 100
    }}
}}
```

### 2. 提交数据 (POST /api/data)

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 是 | 标题 |
| content | string | 是 | 内容 |

## 签名算法

### 签名生成规则

1. **参数排序**: 按参数名ASCII码从小到大排序
2. **拼接字符串**: `key1=value1&key2=value2`
3. **添加时间戳和密钥**: `params_str + timestamp + secret_key`
4. **MD5哈希**: 计算32位小写MD5

### 示例

```python
import hashlib
import time

def generate_sign(params, secret_key):
    # 1. 排序参数
    sorted_params = sorted(params.items())
    param_str = '&'.join([f'{{k}}={{v}}' for k, v in sorted_params])

    # 2. 添加时间戳和密钥
    timestamp = int(time.time())
    sign_str = f'{{param_str}}{{timestamp}}{{secret_key}}'

    # 3. MD5哈希
    sign = hashlib.md5(sign_str.encode()).hexdigest()

    return {{
        'sign': sign,
        'timestamp': timestamp
    }}
```

## 错误处理

### 错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| 400 | 参数错误 | 检查请求参数 |
| 401 | 未授权 | 检查签名是否正确 |
| 403 | 禁止访问 | 检查IP白名单 |
| 500 | 服务器错误 | 稍后重试 |

### 异常处理示例

```python
try:
    result = client.get_data(id='123')
except APIError as e:
    print(f'API错误: {{e.code}} - {{e.message}}')
except NetworkError as e:
    print(f'网络错误: {{e}}')
```

## 使用限制

- **请求频率**: 每秒最多10次请求
- **超时时间**: 30秒
- **数据量限制**: 单次最多100条

## 更新日志

### v1.0.0 ({datetime.now().strftime('%Y-%m-%d')})
- 初始版本
- 支持基础API调用
- 实现签名认证

---
*文档生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return doc

    def generate_readme(self) -> str:
        """
        生成README文档

        Returns:
            Markdown格式的README
        """
        readme = f"""# {self.config.get('project_info', {}).get('name', 'API')} SDK

{self.config.get('project_info', {}).get('url', '')} 的API调用SDK，支持签名认证。

## 功能特性

- 自动签名生成
- 请求重试机制
- 完整错误处理
- 支持Python/JavaScript/Java

## 安装

### Python
```bash
# 复制SDK文件到项目目录
cp output/sdk/python/{self.config.get('project_info', {}).get('name', 'api')}_sdk.py your_project/
```

### JavaScript
```bash
# 复制SDK文件到项目目录
cp output/sdk/javascript/api-sdk.js your_project/
```

## 快速开始

### Python示例

```python
from {self.config.get('project_info', {}).get('name', 'api')}_sdk import APIClient

# 创建客户端
client = APIClient()

# 调用API
result = client.get_data(id='123', page=1)
print(result)

# 关闭客户端
client.close()
```

### JavaScript示例

```javascript
const {{ APIClient }} = require('./api-sdk');

async function main() {{
    const client = new APIClient();

    const result = await client.getData({{ id: '123', page: 1 }});
    console.log(result);
}}

main();
```

## 配置说明

### 必需配置

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| SECRET_KEY | 签名密钥 | 从逆向分析获取 |

### 可选配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| timeout | 30 | 请求超时时间(秒) |
| retry_times | 3 | 重试次数 |
| base_url | - | API基础URL |

## API参考

详细接口说明请参考 [SDK文档](./sdk-document.md)

## 文件结构

```
{self.config.get('project_info', {}).get('name', 'api')}/
├── capture-data/       # 抓包数据
├── analysis/           # 分析结果
├── hooks/              # Hook脚本
├── output/
│   ├── sdk/            # SDK代码
│   │   ├── python/
│   │   ├── javascript/
│   │   └── java/
│   ├── analysis-report.md
│   ├── sdk-document.md
│   └── README.md
└── validation/         # 验证结果
```

## 开发指南

### 运行测试
```bash
python -m pytest tests/
```

### 验证签名
```bash
python scripts/sdk-validator.py --sdk-path output/sdk/python/
```

## 注意事项

1. **密钥安全**: 请勿将密钥提交到公开仓库
2. **请求频率**: 遵守API频率限制
3. **数据安全**: 抓包数据可能包含敏感信息

## 许可证

仅供学习研究使用。

## 更新日志

### v1.0.0 ({datetime.now().strftime('%Y-%m-%d')})
- 初始发布

---
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return readme

    def _format_evidence(self, evidence: list) -> str:
        """格式化证据列表"""
        if not evidence:
            return "无"

        formatted = []
        for e in evidence[:5]:
            formatted.append(f"- {e.get('type', 'unknown')}: {e.get('value', '')}")

        return '\n'.join(formatted)

    def _format_crypto_analysis(self, analysis_data: dict) -> str:
        """格式化加密分析"""
        if not analysis_data:
            return "待分析"

        encrypted_params = analysis_data.get('encrypted_params', [])
        if not encrypted_params:
            return "未发现加密参数"

        formatted = "| 参数名 | 位置 | 特征 |\n|--------|------|------|\n"
        for param in encrypted_params[:10]:
            formatted += f"| {param.get('name', '')} | {param.get('location', '')} | {param.get('patterns', ['未知'])[0] if param.get('patterns') else '未知'} |\n"

        return formatted

    def save_all_documents(self, analysis_data: dict = None, sdk_info: dict = None):
        """保存所有输出文档"""
        output_dir = self.workspace / "output"
        output_dir.mkdir(exist_ok=True)

        # 分析报告
        report = self.generate_analysis_report(analysis_data)
        with open(output_dir / "analysis-report.md", 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"[SAVED] 分析报告: {output_dir / 'analysis-report.md'}")

        # SDK文档
        sdk_doc = self.generate_sdk_document(sdk_info)
        with open(output_dir / "sdk-document.md", 'w', encoding='utf-8') as f:
            f.write(sdk_doc)
        print(f"[SAVED] SDK文档: {output_dir / 'sdk-document.md'}")

        # README
        readme = self.generate_readme()
        with open(output_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme)
        print(f"[SAVED] README: {output_dir / 'README.md'}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='生成输出文档')
    parser.add_argument('--workspace', '-w', required=True, help='工作目录')
    parser.add_argument('--analysis-data', '-a', help='分析数据JSON文件')
    parser.add_argument('--sdk-info', '-s', help='SDK信息JSON文件')

    args = parser.parse_args()

    generator = OutputTemplateGenerator(args.workspace)

    analysis_data = None
    if args.analysis_data and os.path.exists(args.analysis_data):
        with open(args.analysis_data, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)

    sdk_info = None
    if args.sdk_info and os.path.exists(args.sdk_info):
        with open(args.sdk_info, 'r', encoding='utf-8') as f:
            sdk_info = json.load(f)

    generator.save_all_documents(analysis_data, sdk_info)


if __name__ == '__main__':
    main()