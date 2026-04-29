#!/usr/bin/env python3
"""
逆向SDK模板（包含加密逻辑）
用于生成带有加密参数签名的API SDK

此模板用于：
- 已分析出加密算法的情况
- 需要在SDK中实现加密函数的情况
"""

import datetime

# ==================== 逆向SDK完整模板 ====================

REVERSE_SDK_TEMPLATE = '''
#!/usr/bin/env python3
"""
{title} - 带加密签名的API SDK

源URL: {source_url}
生成时间: {generated_time}
加密参数: {encrypted_params}
加密算法: {crypto_algorithm}

逆向分析说明:
{reverse_notes}

使用示例:
    from {module_name} import {client_class}

    client = {client_class}()
    result = client.{main_method}()
    print(result)

警告: 此SDK基于逆向分析生成，仅供学习研究使用。
"""

from curl_cffi import requests  # 模拟浏览器TLS指纹，绕过WAF
import hashlib
import hmac
import base64
import time
import json
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, quote, unquote
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CryptoEngine:
    """加密引擎 - 实现逆向分析出的加密逻辑"""

    {crypto_functions}


class {client_class}:
    """带加密的API客户端"""

    def __init__(self, base_url: str = "{base_url}", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.crypto = CryptoEngine()
        self._setup_headers()

    def _setup_headers(self):
        """设置基础请求头"""
        self.session.headers.update({
            'User-Agent': '{user_agent}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Referer': '{referer}'
        })

    def _generate_signature(self, params: Dict, timestamp: int) -> Dict:
        """
        生成加密签名参数

        Args:
            params: 原始请求参数
            timestamp: 时间戳

        Returns:
            包含签名的完整参数
        """
        {signature_logic}
        return signed_params

    def _request_with_signature(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        发送带签名的请求

        Args:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            data: POST数据

        Returns:
            响应数据
        """
        # 获取时间戳
        timestamp = int(time.time())

        # 生成签名参数
        all_params = {**params} if params else {}
        if method == 'GET':
            signed_params = self._generate_signature(all_params, timestamp)
            url = f"{self.base_url}/{endpoint}?{urlencode(signed_params)}"
            response = self.session.get(url, timeout=self.timeout)
        else:
            signed_data = self._generate_signature(data if data else {}, timestamp)
            url = f"{self.base_url}/{endpoint}"
            response = self.session.post(url, json=signed_data, timeout=self.timeout)

        response.raise_for_status()
        return response.json()

    {api_methods}

    def close(self):
        """关闭会话"""
        self.session.close()


if __name__ == '__main__':
    client = {client_class}()
    try:
        # 测试调用
        result = client.{main_method}()
        print(f"响应数据: {result}")
    except Exception as e:
        logger.error(f"请求失败: {e}")
    finally:
        client.close()
'''

# ==================== 加密函数模板 ====================

CRYPTO_FUNCTION_TEMPLATES = {
    'md5': '''
    @staticmethod
    def md5_hash(text: str) -> str:
        """MD5哈希"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    ''',

    'sha1': '''
    @staticmethod
    def sha1_hash(text: str) -> str:
        """SHA1哈希"""
        return hashlib.sha1(text.encode('utf-8')).hexdigest()
    ''',

    'sha256': '''
    @staticmethod
    def sha256_hash(text: str) -> str:
        """SHA256哈希"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    ''',

    'hmac_sha256': '''
    @staticmethod
    def hmac_sha256(text: str, key: str) -> str:
        """HMAC-SHA256签名"""
        return hmac.new(
            key.encode('utf-8'),
            text.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    ''',

    'base64_encode': '''
    @staticmethod
    def base64_encode(text: str) -> str:
        """Base64编码"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')
    ''',

    'base64_decode': '''
    @staticmethod
    def base64_decode(text: str) -> str:
        """Base64解码"""
        return base64.b64decode(text).decode('utf-8')
    ''',

    'timestamp_sign': '''
    @staticmethod
    def generate_timestamp_sign(params: Dict, secret_key: str) -> str:
        """
        时间戳签名（常见模式）

        签名逻辑: MD5(排序后的参数 + 时间戳 + secret_key)
        """
        timestamp = int(time.time())
        # 按key排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_text = f"{param_str}{timestamp}{secret_key}"
        return hashlib.md5(sign_text.encode('utf-8')).hexdigest()
    ''',

    'complex_sign': '''
    def complex_sign(self, params: Dict, timestamp: int, nonce: str) -> str:
        """
        复杂签名算法（示例）

        逻辑:
        1. 参数排序
        2. 添加时间戳和随机字符串
        3. 多次哈希
        """
        # 步骤1: 参数排序并拼接
        sorted_params = sorted(params.items())
        param_str = ''.join([f"{k}{v}" for k, v in sorted_params])

        # 步骤2: 添加时间戳和nonce
        text = f"{param_str}{timestamp}{nonce}{self.secret_key}"

        # 步骤3: 多次哈希
        first_hash = hashlib.md5(text.encode()).hexdigest()
        second_hash = hashlib.sha256(first_hash.encode()).hexdigest()

        return second_hash.upper()
    '''
}

# ==================== 签名逻辑模板 ====================

SIGNATURE_LOGIC_TEMPLATES = {
    'simple_md5': '''
        # 简单MD5签名
        # sign = MD5(参数排序拼接 + secret_key)
        param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign = self.crypto.md5_hash(f"{param_str}{self.secret_key}")

        signed_params = {**params, 'sign': sign, 'timestamp': timestamp}
    ''',

    'timestamp_md5': '''
        # 时间戳+MD5签名
        # sign = MD5(params + timestamp + secret_key)
        param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign = self.crypto.md5_hash(f"{param_str}{timestamp}{self.secret_key}")

        signed_params = {**params, 'sign': sign, 'timestamp': timestamp}
    ''',

    'hmac_sha256': '''
        # HMAC-SHA256签名
        param_str = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
        sign = self.crypto.hmac_sha256(param_str, self.secret_key)

        signed_params = {**params, 'signature': sign, 'ts': timestamp}
    ''',

    'base64_then_md5': '''
        # Base64编码后MD5哈希
        param_str = json.dumps(params, separators=(',', ':'))
        encoded = self.crypto.base64_encode(param_str)
        sign = self.crypto.md5_hash(encoded + self.secret_key)

        signed_params = {**params, 'data': encoded, 'sign': sign}
    ''',

    'custom': '''
        # 自定义签名逻辑（根据逆向分析填充）
        {custom_sign_logic}

        signed_params = {**params, **sign_result}
    '''
}


def generate_reverse_sdk(
    source_url: str,
    title: str,
    encrypted_params: List[str],
    crypto_algorithm: str,
    reverse_notes: str,
    signature_type: str = 'simple_md5',
    custom_sign_logic: str = '',
    secret_key: str = 'YOUR_SECRET_KEY',
    user_agent: str = 'Mozilla/5.0',
    referer: str = ''
) -> str:
    """
    生成逆向SDK代码

    Args:
        source_url: 源URL
        title: SDK标题
        encrypted_params: 加密参数列表
        crypto_algorithm: 加密算法描述
        reverse_notes: 逆向分析说明
        signature_type: 签名类型
        custom_sign_logic: 自定义签名逻辑代码
        secret_key: 密钥（占位符）
        user_agent: User-Agent
        referer: Referer

    Returns:
        生成的SDK代码
    """
    generated_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    from urllib.parse import urlparse
    parsed = urlparse(source_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    module_name = title.lower().replace(' ', '_').replace('-', '_') + '_reverse_sdk'
    client_class = title.replace(' ', '').replace('-', '') + 'ReverseClient'

    # 选择加密函数
    crypto_functions = ''
    algorithms_needed = []

    if 'md5' in crypto_algorithm.lower():
        algorithms_needed.append('md5')
    if 'sha256' in crypto_algorithm.lower():
        algorithms_needed.append('sha256')
    if 'hmac' in crypto_algorithm.lower():
        algorithms_needed.append('hmac_sha256')
    if 'base64' in crypto_algorithm.lower():
        algorithms_needed.append('base64_encode')
        algorithms_needed.append('base64_decode')
    if 'timestamp' in crypto_algorithm.lower():
        algorithms_needed.append('timestamp_sign')

    for algo in algorithms_needed:
        if algo in CRYPTO_FUNCTION_TEMPLATES:
            crypto_functions += CRYPTO_FUNCTION_TEMPLATES[algo]

    # 默认添加常见加密函数
    if not crypto_functions:
        crypto_functions = CRYPTO_FUNCTION_TEMPLATES['md5'] + CRYPTO_FUNCTION_TEMPLATES['sha256']

    # 选择签名逻辑
    signature_logic = SIGNATURE_LOGIC_TEMPLATES.get(signature_type, SIGNATURE_LOGIC_TEMPLATES['custom'])
    if signature_type == 'custom':
        signature_logic = signature_logic.format(custom_sign_logic=custom_sign_logic)

    # API方法（示例）
    api_methods = '''
    def get_data(self, **kwargs) -> Dict:
        """获取数据"""
        return self._request_with_signature('GET', 'api/data', params=kwargs)

    def post_data(self, data: Dict) -> Dict:
        """提交数据"""
        return self._request_with_signature('POST', 'api/data', data=data)
    '''

    return REVERSE_SDK_TEMPLATE.format(
        title=title,
        source_url=source_url,
        generated_time=generated_time,
        encrypted_params=', '.join(encrypted_params),
        crypto_algorithm=crypto_algorithm,
        reverse_notes=reverse_notes,
        module_name=module_name,
        client_class=client_class,
        base_url=base_url,
        user_agent=user_agent,
        referer=referer or source_url,
        crypto_functions=crypto_functions,
        signature_logic=signature_logic,
        secret_key=secret_key,
        api_methods=api_methods,
        main_method='get_data'
    )


if __name__ == '__main__':
    # 测试生成
    test_code = generate_reverse_sdk(
        source_url='https://api.example.com',
        title='Example API',
        encrypted_params=['sign', 'token'],
        crypto_algorithm='MD5(timestamp + secret_key)',
        reverse_notes='''
        1. 定位加密函数: chunk_123.js line 456
        2. 签名逻辑: sign = MD5(sorted_params + timestamp + secret_key)
        3. secret_key为固定值，从JS常量中提取
        ''',
        signature_type='timestamp_md5'
    )
    print(test_code)