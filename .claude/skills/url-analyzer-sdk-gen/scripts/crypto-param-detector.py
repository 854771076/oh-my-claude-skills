#!/usr/bin/env python3
"""
加密参数检测脚本 V2.0
分析抓包数据，识别可能的加密参数和签名机制

改进:
- 增加更多加密特征检测规则
- 增强签名算法识别能力
- 支持更多编码格式检测
- 生成更详细的逆向分析建议

使用方式:
python crypto-param-detector.py <api-requests.json路径>

输出:
JSON格式的分析结果，包含加密参数识别、加密特征、建议逆向方向
"""

import os
import sys
import json
import re
import base64
import hashlib
import binascii
from urllib.parse import urlparse, parse_qs, unquote, quote
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from collections import Counter


class CryptoParamDetector:
    """加密参数检测器 V2.0"""

    # ============== 加密参数名关键词 ==============
    ENCRYPTED_PARAM_NAMES = [
        # 签名相关
        'sign', 'signature', 'sig', 'auth_sign', 'api_sign', 'data_sign',
        'sign_type', 'sign_method', 'signed_data',
        # Token相关
        'token', 'access_token', 'refresh_token', 'auth_token', 'bearer',
        'csrf_token', 'xsrf_token', '_token',
        # 加密相关
        'secret', 'key', 'encrypt', 'encrypted', 'cipher', 'crypto',
        'encode', 'encoded', 'payload', 'secure',
        # 数据相关
        'data', 'params', 'body', 'query', 'filter',
        # 哈希相关
        'hash', 'md5', 'sha', 'sha1', 'sha256', 'sha512',
        'digest', 'checksum',
        # 时间戳签名
        'timestamp_sign', 'time_sign', 'nonce_sign',
        # 其他常见
        'appkey', 'app_key', 'api_key', 'apikey',
        'signature_method', 'signature_version'
    ]

    # 时间戳参数名
    TIMESTAMP_PARAM_NAMES = [
        'timestamp', 'ts', 'time', 't', 'date', 'datetime',
        'time_stamp', 'timeStamp', '_time', '_ts',
        'created_at', 'create_time', 'request_time'
    ]

    # 随机数参数名
    NONCE_PARAM_NAMES = [
        'nonce', 'noncestr', 'random', 'rand', 'rnd',
        'uuid', 'guid', 'request_id', 'trace_id'
    ]

    # ============== 哈希长度特征 ==============
    HASH_LENGTHS = {
        32: {'algorithm': 'MD5', 'confidence': 0.85},
        40: {'algorithm': 'SHA1', 'confidence': 0.85},
        56: {'algorithm': 'SHA224', 'confidence': 0.7},
        64: {'algorithm': 'SHA256', 'confidence': 0.85},
        96: {'algorithm': 'SHA384', 'confidence': 0.7},
        128: {'algorithm': 'SHA512', 'confidence': 0.85},
        16: {'algorithm': 'MD5(16位)', 'confidence': 0.6},
    }

    # ============== 编码特征正则 ==============
    PATTERNS = {
        # Base64
        'base64': re.compile(r'^[A-Za-z0-9+/]+=*$'),
        'base64_urlsafe': re.compile(r'^[A-Za-z0-9_-]+=*$'),

        # URL编码
        'url_encoded': re.compile(r'%[0-9A-Fa-f]{2}'),

        # 十六进制
        'hex': re.compile(r'^[0-9A-Fa-f]+$'),

        # UUID
        'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I),

        # JWT Token
        'jwt': re.compile(r'^eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$'),

        # 数字签名（纯数字+字母混合，固定长度）
        'signature_like': re.compile(r'^[a-f0-9]{16,128}$', re.I),

        # 时间戳
        'timestamp_seconds': re.compile(r'^1[0-9]{9}$'),
        'timestamp_millis': re.compile(r'^1[0-9]{12}$'),

        # OAuth相关
        'oauth_token': re.compile(r'^oauth_token_'),

        # AES加密特征（常见前缀）
        'aes_prefix': re.compile(r'^(U2F|Aes|ENC|cipher)'),
    }

    # ============== 常见签名算法特征 ==============
    SIGNATURE_ALGORITHMS = {
        'md5_sha1': {
            'pattern': r'[a-f0-9]{32,40}',
            'description': 'MD5或SHA1签名'
        },
        'hmac_sha256': {
            'pattern': r'[a-f0-9]{64}',
            'description': 'HMAC-SHA256签名'
        },
        'rsa_sign': {
            'pattern': r'[A-Za-z0-9+/]{100,}={0,2}$',
            'description': '可能是RSA签名（Base64编码的长字符串）'
        }
    }

    def __init__(self, api_requests_file: str = None, requests_data: List[Dict] = None):
        """
        初始化检测器

        Args:
            api_requests_file: API请求JSON文件路径
            requests_data: 直接传入的请求数据列表
        """
        if requests_data:
            self.api_requests = requests_data
        elif api_requests_file:
            self.api_requests = self._load_requests(api_requests_file)
        else:
            self.api_requests = []

        self.result = {
            'has_encryption': False,
            'encrypted_params': [],
            'signature_params': [],
            'timestamp_params': [],
            'nonce_params': [],
            'encryption_patterns': [],
            'detected_algorithms': [],
            'reverse_recommendations': [],
            'analysis_details': [],
            'summary': {}
        }

        # 内部统计
        self._stats = {
            'total_requests': 0,
            'requests_with_encryption': 0,
            'param_counter': Counter(),
            'value_length_counter': Counter()
        }

    def _load_requests(self, filepath: str) -> List[Dict]:
        """加载API请求数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def detect(self) -> Dict:
        """执行加密参数检测"""
        self._stats['total_requests'] = len(self.api_requests)

        for request in self.api_requests:
            self._analyze_request(request)

        # 综合判断是否有加密
        if self.result['encrypted_params'] or self.result['signature_params']:
            self.result['has_encryption'] = True
            self._generate_reverse_recommendations()

        # 生成摘要
        self._generate_summary()

        return self.result

    def _analyze_request(self, request: Dict):
        """分析单个请求"""
        url = request.get('url', '')
        method = request.get('method', 'GET')
        headers = request.get('headers', {})
        post_data = request.get('postData', '')

        # 分析URL参数
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        for param_name, param_values in query_params.items():
            param_value = param_values[0] if param_values else ''
            self._analyze_param(param_name, param_value, 'url_query', url, method)

        # 分析POST数据
        if post_data:
            self._analyze_post_data(post_data, url, method)

        # 分析请求头
        for header_name, header_value in headers.items():
            self._analyze_param(header_name, header_value, 'header', url, method, is_header=True)

    def _analyze_post_data(self, post_data: str, url: str, method: str):
        """分析POST数据"""
        # 尝试解析为JSON
        try:
            post_json = json.loads(post_data)
            if isinstance(post_json, dict):
                self._analyze_json_object(post_json, 'post_body_json', url, method)
            elif isinstance(post_json, list):
                for i, item in enumerate(post_json):
                    if isinstance(item, dict):
                        self._analyze_json_object(item, f'post_body_json[{i}]', url, method)
        except json.JSONDecodeError:
            # 可能是form数据或其他格式
            if '=' in post_data:
                try:
                    form_params = parse_qs(post_data)
                    for key, values in form_params.items():
                        self._analyze_param(key, values[0] if values else '', 'post_body_form', url, method)
                except:
                    # 可能是纯文本或其他格式
                    self._analyze_param('raw_post_data', post_data[:500], 'post_body_raw', url, method)

    def _analyze_json_object(self, obj: Dict, location: str, url: str, method: str, prefix: str = ''):
        """递归分析JSON对象"""
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                self._analyze_json_object(value, location, url, method, full_key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._analyze_json_object(item, location, url, method, f"{full_key}[{i}]")
                    else:
                        self._analyze_param(full_key, str(item), location, url, method)
            else:
                self._analyze_param(full_key, str(value), location, url, method)

    def _analyze_param(self, name: str, value: str, location: str, request_url: str,
                       method: str = 'GET', is_header: bool = False):
        """分析单个参数"""
        if not value:
            return

        self._stats['param_counter'][name] += 1
        self._stats['value_length_counter'][len(value)] += 1

        param_info = {
            'name': name,
            'value': value[:200],  # 截取前200字符
            'value_length': len(value),
            'location': location,
            'request_url': request_url,
            'method': method,
            'is_dynamic': False,
            'encryption_type': None,
            'patterns': [],
            'detected_at': datetime.now().isoformat()
        }

        # 跳过常见的静态参数
        if self._is_static_param(name, value):
            return

        # 检查是否为时间戳
        if name.lower() in [t.lower() for t in self.TIMESTAMP_PARAM_NAMES]:
            self._check_timestamp(value, param_info)
            if param_info.get('is_valid_timestamp'):
                self.result['timestamp_params'].append(param_info)
                return

        # 检查是否为随机数
        if name.lower() in [n.lower() for n in self.NONCE_PARAM_NAMES]:
            param_info['is_nonce'] = True
            self.result['nonce_params'].append(param_info)

        # 检查是否为UUID
        if self._check_uuid(value, param_info):
            return

        # 检查是否为JWT
        if self._check_jwt(value, param_info):
            self.result['signature_params'].append(param_info)
            return

        # 检查参数名是否暗示加密/签名
        is_encrypted_param = any(
            enc_name in name.lower()
            for enc_name in self.ENCRYPTED_PARAM_NAMES
        )

        if is_encrypted_param:
            param_info['is_dynamic'] = True
            self.result['signature_params'].append(param_info)

        # 分析值特征
        self._analyze_value_patterns(value, param_info)

        # 如果值有加密特征，标记为加密参数
        if param_info['patterns']:
            if not is_encrypted_param:
                self.result['encrypted_params'].append(param_info)
            self.result['encryption_patterns'].extend(param_info['patterns'])

    def _is_static_param(self, name: str, value: str) -> bool:
        """判断是否为静态参数"""
        static_patterns = [
            (r'^\d{1,4}$', 'small_number'),  # 小数字
            (r'^true|false$', 'boolean'),     # 布尔值
            (r'^[a-z]{2,3}$', 'lang_code'),   # 语言代码
            (r'^\d+\.\d+\.\d+$', 'version'),  # 版本号
        ]

        for pattern, _ in static_patterns:
            if re.match(pattern, value, re.I):
                return True
        return False

    def _check_timestamp(self, value: str, param_info: Dict) -> bool:
        """检查并验证时间戳"""
        try:
            ts = int(value)
            now = datetime.now().timestamp()

            # 检查是否为合理的时间戳范围（前后1年）
            one_year = 365 * 24 * 3600
            if not (now - one_year < ts < now + one_year):
                # 尝试毫秒
                ts = ts / 1000
                if not (now - one_year < ts < now + one_year):
                    return False
                param_info['timestamp_unit'] = 'milliseconds'
            else:
                param_info['timestamp_unit'] = 'seconds'

            dt = datetime.fromtimestamp(ts)
            param_info['parsed_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            param_info['is_valid_timestamp'] = True
            param_info['is_dynamic'] = True
            return True

        except ValueError:
            return False

    def _check_uuid(self, value: str, param_info: Dict) -> bool:
        """检查是否为UUID"""
        if self.PATTERNS['uuid'].match(value):
            param_info['patterns'].append({
                'type': 'uuid',
                'confidence': 1.0,
                'description': 'UUID格式'
            })
            param_info['is_dynamic'] = True
            return True
        return False

    def _check_jwt(self, value: str, param_info: Dict) -> bool:
        """检查是否为JWT Token"""
        if self.PATTERNS['jwt'].match(value):
            param_info['patterns'].append({
                'type': 'jwt',
                'confidence': 1.0,
                'description': 'JWT Token格式'
            })
            param_info['is_dynamic'] = True

            # 尝试解析JWT
            try:
                parts = value.split('.')
                if len(parts) == 3:
                    # 解析header
                    header = base64.urlsafe_b64decode(parts[0] + '==').decode('utf-8')
                    param_info['jwt_header'] = json.loads(header)
                    # 解析payload（不验证签名）
                    payload = base64.urlsafe_b64decode(parts[1] + '==').decode('utf-8')
                    param_info['jwt_payload'] = json.loads(payload)
            except:
                pass

            return True
        return False

    def _analyze_value_patterns(self, value: str, param_info: Dict):
        """分析值的加密特征"""
        if not value or len(value) < 4:
            return

        patterns_found = []

        # 1. 检查Base64编码
        if self._is_base64(value):
            patterns_found.append({
                'type': 'base64',
                'confidence': 0.8,
                'description': 'Base64编码'
            })
            try:
                decoded = base64.b64decode(value).decode('utf-8', errors='ignore')
                param_info['decoded_preview'] = decoded[:100]
                # 递归检查解码后的内容
                if decoded.startswith('{') or decoded.startswith('['):
                    param_info['decoded_is_json'] = True
            except:
                pass

        # 2. 检查URL编码
        if self.PATTERNS['url_encoded'].search(value):
            patterns_found.append({
                'type': 'url_encoded',
                'confidence': 0.9,
                'description': 'URL编码'
            })
            decoded = unquote(value)
            param_info['url_decoded'] = decoded[:200]

        # 3. 检查哈希长度特征
        clean_value = value.strip()
        if self.PATTERNS['hex'].match(clean_value):
            length = len(clean_value)
            if length in self.HASH_LENGTHS:
                hash_info = self.HASH_LENGTHS[length]
                patterns_found.append({
                    'type': 'hash',
                    'algorithm': hash_info['algorithm'],
                    'confidence': hash_info['confidence'],
                    'description': f"长度符合{hash_info['algorithm']}哈希"
                })
                self.result['detected_algorithms'].append(hash_info['algorithm'])

        # 4. 检查JSON编码
        if value.startswith('{') or value.startswith('['):
            try:
                json.loads(value)
                patterns_found.append({
                    'type': 'json_string',
                    'confidence': 1.0,
                    'description': 'JSON字符串'
                })
            except json.JSONDecodeError:
                pass

        # 5. 检查数字签名特征
        if self.PATTERNS['signature_like'].match(value):
            length = len(value)
            if length in self.HASH_LENGTHS:
                patterns_found.append({
                    'type': 'digital_signature',
                    'confidence': 0.75,
                    'description': '可能是数字签名'
                })

        # 6. 检查AES加密特征
        if self.PATTERNS['aes_prefix'].match(value):
            patterns_found.append({
                'type': 'aes_encrypted',
                'confidence': 0.6,
                'description': '可能是AES加密数据'
            })

        # 7. 检查时间戳特征
        if self.PATTERNS['timestamp_seconds'].match(value):
            patterns_found.append({
                'type': 'timestamp_seconds',
                'confidence': 0.95,
                'description': '10位时间戳（秒）'
            })
        elif self.PATTERNS['timestamp_millis'].match(value):
            patterns_found.append({
                'type': 'timestamp_millis',
                'confidence': 0.95,
                'description': '13位时间戳（毫秒）'
            })

        # 8. 检查混合编码（Base64嵌套）
        if '=' in value and len(value) > 50:
            # 尝试检测多层编码
            try:
                # 尝试Base64 -> URL解码 -> Base64
                temp = base64.b64decode(value).decode('utf-8')
                temp = unquote(temp)
                if self._is_base64(temp):
                    patterns_found.append({
                        'type': 'nested_encoding',
                        'confidence': 0.7,
                        'description': '可能是多层编码（Base64+URL+Base64）'
                    })
            except:
                pass

        param_info['patterns'] = patterns_found

    def _is_base64(self, value: str) -> bool:
        """检查是否为Base64编码"""
        if len(value) < 4 or len(value) % 4 != 0:
            return False
        if not self.PATTERNS['base64'].match(value):
            return False
        try:
            base64.b64decode(value)
            return True
        except:
            return False

    def _generate_reverse_recommendations(self):
        """生成逆向分析建议"""
        recommendations = []

        # 1. 根据检测到的哈希算法生成建议
        algorithms = set(self.result['detected_algorithms'])
        if algorithms:
            recommendations.append({
                'priority': 1,
                'action': 'search_hash_function',
                'description': f"搜索JS中的{', '.join(algorithms)}哈希函数",
                'keywords': list(algorithms) + ['crypto-js', 'hashlib', 'CryptoJS'],
                'files_to_check': ['*.js', 'main.js', 'chunk*.js', 'vendor.js']
            })

        # 2. Base64编码分析
        base64_count = sum(1 for p in self.result['encryption_patterns'] if p['type'] == 'base64')
        if base64_count > 0:
            recommendations.append({
                'priority': 2,
                'action': 'search_base64_function',
                'description': f'发现{base64_count}处Base64编码，搜索编码函数',
                'keywords': ['btoa', 'atob', 'base64', 'encode', 'decode', 'Buffer'],
                'note': '注意：Base64通常只是中间编码，实际加密可能在编码前'
            })

        # 3. 时间戳+签名组合分析
        if self.result['timestamp_params'] and self.result['signature_params']:
            recommendations.append({
                'priority': 3,
                'action': 'analyze_sign_algorithm',
                'description': '存在时间戳+签名组合，分析签名算法',
                'likely_patterns': [
                    'sign = MD5(params_sorted + timestamp + secret)',
                    'sign = HMAC_SHA256(params + timestamp, secret)',
                    'sign = MD5(appkey + timestamp + nonce + secret)'
                ],
                'keywords': ['sign', 'timestamp', 'secret', 'key', 'concat', 'sort', 'join']
            })

        # 4. JWT分析
        jwt_params = [p for p in self.result['signature_params'] if p.get('patterns') and len(p.get('patterns', [])) > 0 and 'jwt' in p.get('patterns', [{}])[0].get('type', '')]
        if jwt_params:
            recommendations.append({
                'priority': 4,
                'action': 'analyze_jwt',
                'description': '检测到JWT Token，检查签名算法',
                'jwt_info': jwt_params[0].get('jwt_header', {}),
                'keywords': ['jwt', 'jsonwebtoken', 'sign', 'HS256', 'RS256']
            })

        # 5. Webpack模块分析
        recommendations.append({
            'priority': 5,
            'action': 'analyze_webpack_modules',
            'description': '检查JS文件是否为Webpack打包，定位加密模块',
            'keywords': ['webpackJsonp', '__webpack_require__', 'modules', '__webpack_modules__'],
            'tools': ['js-search-tool.py', 'chrome-devtools-sources']
        })

        # 6. Hook注入建议
        if self.result['signature_params']:
            recommendations.append({
                'priority': 6,
                'action': 'inject_crypto_hook',
                'description': '注入加密函数Hook拦截签名生成过程',
                'hook_files': [
                    'hooks/crypto-hook.js',
                    'hooks/xhr-hook.js',
                    'hooks/all-in-one-hook.js'
                ],
                'usage': '在浏览器控制台或Playwright中注入Hook脚本'
            })

        self.result['reverse_recommendations'] = recommendations

    def _generate_summary(self):
        """生成分析摘要"""
        self.result['summary'] = {
            'total_requests_analyzed': self._stats['total_requests'],
            'requests_with_encryption': sum(1 for r in self.api_requests if self._request_has_encryption(r)),
            'unique_encrypted_params': len(set(p['name'] for p in self.result['encrypted_params'])),
            'unique_signature_params': len(set(p['name'] for p in self.result['signature_params'])),
            'timestamp_params_count': len(self.result['timestamp_params']),
            'nonce_params_count': len(self.result['nonce_params']),
            'detected_encryption_types': list(set(p['type'] for p in self.result['encryption_patterns'])),
            'detected_algorithms': list(set(self.result['detected_algorithms'])),
            'encryption_confidence': self._calculate_encryption_confidence(),
            'analysis_completed_at': datetime.now().isoformat()
        }

    def _request_has_encryption(self, request: Dict) -> bool:
        """检查请求是否包含加密参数"""
        url = request.get('url', '')
        for param in self.result['encrypted_params'] + self.result['signature_params']:
            if param['request_url'] == url:
                return True
        return False

    def _calculate_encryption_confidence(self) -> str:
        """计算加密置信度"""
        score = 0

        # 有签名参数 +3
        if self.result['signature_params']:
            score += 3

        # 有时间戳参数 +2
        if self.result['timestamp_params']:
            score += 2

        # 有加密特征 +2
        if self.result['encryption_patterns']:
            score += 2

        # 检测到哈希算法 +3
        if self.result['detected_algorithms']:
            score += 3

        if score >= 8:
            return 'HIGH'
        elif score >= 5:
            return 'MEDIUM'
        elif score >= 2:
            return 'LOW'
        else:
            return 'NONE'


def main():
    if len(sys.argv) < 2:
        print("Usage: python crypto-param-detector.py <api-requests.json>")
        print("\nOptions:")
        print("  -o, --output    指定输出文件路径")
        print("  -v, --verbose   显示详细输出")
        print("\nExample:")
        print("  python crypto-param-detector.py ./capture-output/api-requests.json")
        print("  python crypto-param-detector.py ./capture-output/api-requests.json -o analysis.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None
    verbose = False

    # 解析参数
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg in ['-o', '--output']:
            output_file = sys.argv[i + 1]
        elif arg in ['-v', '--verbose']:
            verbose = True

    if not os.path.exists(input_file):
        print(f"Error: File not found - {input_file}")
        sys.exit(1)

    detector = CryptoParamDetector(input_file)
    result = detector.detect()

    # 输出结果
    if not output_file:
        output_file = input_file.replace('.json', '-crypto-analysis.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    if verbose:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 简洁输出
        summary = result['summary']
        print(f"\n{'='*50}")
        print("加密参数检测报告")
        print('='*50)
        print(f"分析请求数: {summary['total_requests_analyzed']}")
        print(f"加密置信度: {summary['encryption_confidence']}")
        print(f"签名参数: {summary['unique_signature_params']} 个")
        print(f"加密参数: {summary['unique_encrypted_params']} 个")
        print(f"检测到的算法: {', '.join(summary['detected_algorithms']) or '无'}")
        print(f"\n分析结果已保存到: {output_file}")


if __name__ == '__main__':
    main()