# SDK最佳实践指南

## 概述
本文档提供生成高质量API SDK的最佳实践指导，确保生成的SDK具备：
- 完整的功能覆盖
- 健壮的错误处理
- 清晰的文档和示例
- 可维护性和可扩展性

## SDK核心组件

### 1. 配置管理
```python
class Config:
    """SDK配置类"""
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.timeout = 30
        self.retry_times = 3
        self.retry_delay = 1.0  # 指数退避基数
        self.max_connections = 10
```

### 2. 会话管理
- **必须** 使用Session对象保持连接池
- **必须** 复用TCP连接，避免每次请求建立新连接
- **必须** 正确关闭会话释放资源

```python
# 正确示例
session = requests.Session()
try:
    response = session.get(url)
finally:
    session.close()

# 错误示例 - 每次请求创建新连接
requests.get(url)  # 不推荐
```

### 3. 请求头管理
**必须包含的请求头**：
- `User-Agent`: 标识SDK身份
- `Accept`: 声明接受的内容类型
- `Content-Type`: POST/PUT请求必须声明
- `Accept-Language`: 语言偏好
- `Accept-Encoding`: gzip压缩支持

```python
DEFAULT_HEADERS = {
    'User-Agent': 'MySDK/1.0.0 (Python/3.9)',
    'Accept': 'application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Accept-Encoding': 'gzip, deflate'
}
```

## 错误处理策略

### 1. 网络错误
```python
def request_with_retry(self, method, url, retry_times=3):
    for attempt in range(retry_times):
        try:
            response = self.session.request(method, url)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            if attempt < retry_times - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise APITimeoutError(f"请求超时: {url}")
        except requests.ConnectionError:
            if attempt < retry_times - 1:
                time.sleep(2 ** attempt)
            else:
                raise APIConnectionError(f"连接失败: {url}")
        except requests.HTTPError as e:
            raise APIHTTPError(f"HTTP错误: {e.response.status_code}")
```

### 2. 业务错误
```python
class APIError(Exception):
    """API错误基类"""
    def __init__(self, code, message, details=None):
        self.code = code
        self.message = message
        self.details = details

def handle_response(response):
    data = response.json()
    if 'error' in data:
        raise APIError(
            code=data['error']['code'],
            message=data['error']['message'],
            details=data['error'].get('details')
        )
    return data['data']
```

### 3. 参数验证
```python
def validate_params(params, required_keys):
    """验证必需参数"""
    missing = [k for k in required_keys if k not in params]
    if missing:
        raise ValueError(f"缺少必需参数: {missing}")

    # 类型验证
    for key, expected_type in TYPE_MAPPING.items():
        if key in params and not isinstance(params[key], expected_type):
            raise TypeError(f"参数 {key} 类型错误，应为 {expected_type}")
```

## 重试策略

### 指数退避算法
```python
def exponential_backoff(base_delay, max_delay, attempt):
    """计算退避时间"""
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)

# 使用示例
for attempt in range(3):
    try:
        response = request()
        break
    except Exception:
        delay = exponential_backoff(1.0, 30.0, attempt)
        time.sleep(delay)
```

### 可重试的HTTP状态码
- 408 Request Timeout
- 429 Too Many Requests
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout

## SDK文档规范

### 方法文档模板
```python
def get_product(self, product_id: str) -> Dict:
    """
    获取产品详情

    Args:
        product_id (str): 产品唯一标识符

    Returns:
        Dict: 产品信息字典，包含以下字段:
            - id: 产品ID
            - name: 产品名称
            - price: 产品价格
            - stock: 库存数量

    Raises:
        ValueError: product_id为空或格式错误
        APIError: API返回错误（404/500等）
        APITimeoutError: 请求超时

    Example:
        >>> client = ProductClient()
        >>> product = client.get_product('prod_123')
        >>> print(product['name'])
        'iPhone 15'
    """
```

### 模块文档
```python
"""
产品API SDK

提供产品数据的查询、创建、更新、删除功能。

Quick Start:
    from product_sdk import ProductClient

    client = ProductClient(api_key='your_key')
    products = client.list_products(page=1, limit=10)

Features:
    - 产品列表查询（支持分页、过滤）
    - 产品详情获取
    - 产品创建和更新
    - 批量操作支持

Configuration:
    - api_key: API认证密钥（必需）
    - base_url: API服务地址（可选，默认为官方地址）
    - timeout: 请求超时时间（可选，默认30秒）
"""
```

## 测试覆盖

### 单元测试示例
```python
import pytest
from unittest.mock import Mock, patch

class TestProductClient:

    def setup_method(self):
        self.client = ProductClient()

    def test_get_product_success(self):
        """测试成功获取产品"""
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value = Mock(
                status_code=200,
                json=lambda: {'id': '123', 'name': 'Test'}
            )
            result = self.client.get_product('123')
            assert result['id'] == '123'

    def test_get_product_not_found(self):
        """测试产品不存在"""
        with patch('requests.Session.get') as mock_get:
            mock_get.return_value = Mock(status_code=404)
            with pytest.raises(APIError):
                self.client.get_product('999')

    def test_get_product_timeout(self):
        """测试请求超时"""
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = requests.Timeout()
            with pytest.raises(APITimeoutError):
                self.client.get_product('123')
```

## 性能优化

### 1. 连接池配置
```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def setup_session(pool_connections=10, pool_maxsize=10):
    session = requests.Session()

    # 配置连接池
    adapter = HTTPAdapter(
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
        max_retries=Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session
```

### 2. 异步支持
```python
import aiohttp
import asyncio

class AsyncClient:
    async def fetch(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    async def batch_fetch(self, urls):
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)
```

## 安全考虑

### 1. 敏感信息处理
- **禁止** 在日志中输出API密钥、token
- **禁止** 在URL参数中传递敏感信息
- **必须** 使用HTTPS
- **必须** 验证服务器证书

```python
# 安全的日志处理
def safe_log_request(url, params):
    safe_params = {k: v if k not in SENSITIVE_KEYS else '***' for k, v in params.items()}
    logger.info(f"请求: {url}, 参数: {safe_params}")
```

### 2. 输入验证
```python
def sanitize_input(text):
    """清理输入，防止注入"""
    if not isinstance(text, str):
        raise TypeError("输入必须是字符串")
    # 移除危险字符
    return text.replace('<', '').replace('>', '').replace('"', '')
```

## 版本兼容性

### 版本检测
```python
class VersionedClient:
    def __init__(self, api_version='v1'):
        self.api_version = api_version
        self.base_url = f"https://api.example.com/{api_version}"

    def check_compatibility(self):
        """检查API版本兼容性"""
        response = self.session.get(f"{self.base_url}/version")
        server_version = response.json()['version']
        if not self._is_compatible(server_version):
            raise VersionIncompatibleError(
                f"SDK版本 {self.api_version} 与服务器版本 {server_version} 不兼容"
            )
```

## 总结

生成高质量SDK的关键：
1. 完善的错误处理和重试机制
2. 清晰的文档和类型提示
3. 合理的配置和连接池管理
4. 充分的测试覆盖
5. 安全的敏感信息处理
6. 性能优化和异步支持