#!/usr/bin/env python3
"""
SDK验证脚本
验证生成的SDK是否正确工作，包括签名验证、API调用测试

使用方式:
python sdk-validator.py --sdk-path "./output/sdk/python/" --test-url "https://api.example.com"
"""

import os
import sys
import json
import time
import importlib.util
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class SDKValidator:
    """SDK验证器"""

    def __init__(self, sdk_path: str, test_url: str = None, captured_data: str = None):
        """
        初始化

        Args:
            sdk_path: SDK代码路径
            test_url: 测试URL
            captured_data: 抓包数据路径（用于对比验证）
        """
        self.sdk_path = Path(sdk_path)
        self.test_url = test_url
        self.captured_data_path = captured_data
        self.captured_data = None
        self.results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sdk_path': str(sdk_path),
            'test_url': test_url,
            'tests': {},
            'summary': {},
            'conclusion': None
        }

        # 加载抓包数据
        if captured_data and os.path.exists(captured_data):
            with open(captured_data, 'r', encoding='utf-8') as f:
                self.captured_data = json.load(f)

    def _load_sdk_module(self):
        """动态加载SDK模块"""
        # 查找SDK文件
        sdk_files = list(self.sdk_path.glob('*.py'))
        if not sdk_files:
            raise FileNotFoundError(f"未找到SDK文件: {self.sdk_path}")

        # 使用第一个找到的SDK文件
        sdk_file = sdk_files[0]
        module_name = sdk_file.stem

        spec = importlib.util.spec_from_file_location(module_name, sdk_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    def validate_signature(self, sdk_module) -> Dict:
        """
        验证签名生成功能

        Args:
            sdk_module: SDK模块

        Returns:
            验证结果
        """
        test_result = {
            'name': '签名生成验证',
            'status': 'pending',
            'details': [],
            'error': None
        }

        try:
            # 查找客户端类
            client_class = None
            for name in dir(sdk_module):
                obj = getattr(sdk_module, name)
                if isinstance(obj, type) and ('Client' in name or 'SDK' in name):
                    client_class = obj
                    break

            if not client_class:
                test_result['status'] = 'failed'
                test_result['error'] = '未找到SDK客户端类'
                return test_result

            # 创建客户端实例
            client = client_class()

            # 测试签名生成
            if hasattr(client, '_generate_signature'):
                test_params = {'id': '123', 'name': 'test'}
                timestamp = int(time.time())
                signed = client._generate_signature(test_params, timestamp)

                if 'sign' in signed:
                    test_result['status'] = 'passed'
                    test_result['details'].append({
                        'input': test_params,
                        'output': signed,
                        'signature': signed.get('sign', '')[:32] + '...'
                    })
                else:
                    test_result['status'] = 'failed'
                    test_result['error'] = '签名参数未生成'
            elif hasattr(client, 'crypto') and hasattr(client.crypto, 'md5_hash'):
                # 测试加密函数
                test_input = "test_string"
                test_output = client.crypto.md5_hash(test_input)

                if test_output and len(test_output) == 32:
                    test_result['status'] = 'passed'
                    test_result['details'].append({
                        'function': 'md5_hash',
                        'input': test_input,
                        'output': test_output
                    })
                else:
                    test_result['status'] = 'failed'
                    test_result['error'] = '加密函数输出格式错误'
            else:
                test_result['status'] = 'skipped'
                test_result['error'] = 'SDK不包含签名/加密功能'

        except Exception as e:
            test_result['status'] = 'error'
            test_result['error'] = str(e)

        return test_result

    def validate_api_call(self, sdk_module) -> Dict:
        """
        验证API调用功能

        Args:
            sdk_module: SDK模块

        Returns:
            验证结果
        """
        test_result = {
            'name': 'API调用验证',
            'status': 'pending',
            'details': [],
            'error': None
        }

        if not self.test_url:
            test_result['status'] = 'skipped'
            test_result['error'] = '未提供测试URL'
            return test_result

        try:
            # 查找客户端类
            client_class = None
            for name in dir(sdk_module):
                obj = getattr(sdk_module, name)
                if isinstance(obj, type) and ('Client' in name or 'SDK' in name):
                    client_class = obj
                    break

            if not client_class:
                test_result['status'] = 'failed'
                test_result['error'] = '未找到SDK客户端类'
                return test_result

            client = client_class()

            # 尝试调用API
            if hasattr(client, 'get_data'):
                result = client.get_data()
                test_result['status'] = 'passed' if result else 'failed'
                test_result['details'].append({
                    'method': 'get_data',
                    'response_type': type(result).__name__,
                    'has_data': bool(result)
                })
            elif hasattr(client, 'request'):
                result = client.request('GET', self.test_url)
                test_result['status'] = 'passed' if result else 'failed'
                test_result['details'].append({
                    'method': 'request',
                    'url': self.test_url
                })
            else:
                test_result['status'] = 'skipped'
                test_result['error'] = 'SDK不包含标准API调用方法'

            # 关闭客户端
            if hasattr(client, 'close'):
                client.close()

        except Exception as e:
            test_result['status'] = 'error'
            test_result['error'] = str(e)

        return test_result

    def validate_signature_match(self, sdk_module) -> Dict:
        """
        验证生成的签名是否与抓包签名匹配

        Args:
            sdk_module: SDK模块

        Returns:
            验证结果
        """
        test_result = {
            'name': '签名匹配验证',
            'status': 'pending',
            'details': [],
            'error': None
        }

        if not self.captured_data:
            test_result['status'] = 'skipped'
            test_result['error'] = '未提供抓包数据'
            return test_result

        try:
            # 从抓包数据提取签名
            captured_sign = None
            captured_params = {}

            # 尝试从API请求中提取签名
            if isinstance(self.captured_data, list) and len(self.captured_data) > 0:
                first_request = self.captured_data[0]
                if 'postData' in first_request:
                    try:
                        post_data = json.loads(first_request['postData'])
                        if 'sign' in post_data:
                            captured_sign = post_data['sign']
                            captured_params = {k: v for k, v in post_data.items() if k != 'sign'}
                    except:
                        pass

            if not captured_sign:
                test_result['status'] = 'skipped'
                test_result['error'] = '抓包数据中未找到签名'
                return test_result

            # 使用SDK生成签名
            client_class = None
            for name in dir(sdk_module):
                obj = getattr(sdk_module, name)
                if isinstance(obj, type) and ('Client' in name or 'SDK' in name):
                    client_class = obj
                    break

            if client_class and hasattr(client_class, '_generate_signature'):
                client = client_class()
                # 使用抓包的参数和时间戳生成签名
                timestamp = captured_params.get('timestamp', int(time.time()))
                generated = client._generate_signature(captured_params, timestamp)
                generated_sign = generated.get('sign', '')

                # 对比签名
                if generated_sign == captured_sign:
                    test_result['status'] = 'passed'
                    test_result['details'].append({
                        'captured_sign': captured_sign[:32] + '...',
                        'generated_sign': generated_sign[:32] + '...',
                        'match': True
                    })
                else:
                    test_result['status'] = 'failed'
                    test_result['details'].append({
                        'captured_sign': captured_sign[:32] + '...',
                        'generated_sign': generated_sign[:32] + '...',
                        'match': False
                    })
                    test_result['error'] = '签名不匹配'
            else:
                test_result['status'] = 'skipped'
                test_result['error'] = 'SDK不支持签名生成'

        except Exception as e:
            test_result['status'] = 'error'
            test_result['error'] = str(e)

        return test_result

    def validate_code_quality(self, sdk_module) -> Dict:
        """
        验证代码质量

        Args:
            sdk_module: SDK模块

        Returns:
            验证结果
        """
        test_result = {
            'name': '代码质量检查',
            'status': 'pending',
            'details': [],
            'error': None
        }

        try:
            checks = {
                'has_docstring': False,
                'has_error_handling': False,
                'has_type_hints': False,
                'has_client_class': False,
                'has_example': False
            }

            # 检查模块文档字符串
            if sdk_module.__doc__:
                checks['has_docstring'] = True

            # 检查错误处理
            sdk_code = ""
            sdk_files = list(self.sdk_path.glob('*.py'))
            if sdk_files:
                with open(sdk_files[0], 'r', encoding='utf-8') as f:
                    sdk_code = f.read()

            if 'try:' in sdk_code and 'except' in sdk_code:
                checks['has_error_handling'] = True

            # 检查类型提示
            if '-> ' in sdk_code or ': ' in sdk_code:
                checks['has_type_hints'] = True

            # 检查客户端类
            for name in dir(sdk_module):
                obj = getattr(sdk_module, name)
                if isinstance(obj, type) and ('Client' in name or 'SDK' in name):
                    checks['has_client_class'] = True
                    # 检查示例
                    if obj.__doc__ and 'Example' in obj.__doc__:
                        checks['has_example'] = True

            # 计算通过率
            passed = sum(checks.values())
            total = len(checks)

            test_result['details'] = checks
            test_result['status'] = 'passed' if passed >= total * 0.6 else 'failed'

        except Exception as e:
            test_result['status'] = 'error'
            test_result['error'] = str(e)

        return test_result

    def run_all_tests(self) -> Dict:
        """
        运行所有验证测试

        Returns:
            完整测试结果
        """
        print(f"[INFO] 加载SDK: {self.sdk_path}")
        sdk_module = self._load_sdk_module()

        print("[INFO] 运行验证测试...")

        # 签名验证
        print("  - 签名生成验证...")
        self.results['tests']['signature'] = self.validate_signature(sdk_module)

        # API调用验证
        print("  - API调用验证...")
        self.results['tests']['api_call'] = self.validate_api_call(sdk_module)

        # 签名匹配验证
        print("  - 签名匹配验证...")
        self.results['tests']['signature_match'] = self.validate_signature_match(sdk_module)

        # 代码质量检查
        print("  - 代码质量检查...")
        self.results['tests']['code_quality'] = self.validate_code_quality(sdk_module)

        # 生成摘要
        self._generate_summary()

        return self.results

    def _generate_summary(self):
        """生成测试摘要"""
        total = len(self.results['tests'])
        passed = sum(1 for t in self.results['tests'].values() if t['status'] == 'passed')
        failed = sum(1 for t in self.results['tests'].values() if t['status'] == 'failed')
        skipped = sum(1 for t in self.results['tests'].values() if t['status'] == 'skipped')
        error = sum(1 for t in self.results['tests'].values() if t['status'] == 'error')

        self.results['summary'] = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'error': error,
            'pass_rate': f"{passed/total*100:.1f}%" if total > 0 else "0%"
        }

        # 结论
        if passed == total:
            self.results['conclusion'] = "SDK验证通过，所有测试均已成功"
        elif passed >= total * 0.7:
            self.results['conclusion'] = "SDK基本可用，部分测试未通过"
        else:
            self.results['conclusion'] = "SDK验证失败，需要修复"

    def save_results(self, output_path: str):
        """保存结果到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"[SAVED] 测试结果已保存: {output_path}")

    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*60)
        print("SDK验证测试报告")
        print("="*60)

        for test_name, test_result in self.results['tests'].items():
            status_icon = {
                'passed': '✓',
                'failed': '✗',
                'skipped': '○',
                'error': '!',
                'pending': '?'
            }.get(test_result['status'], '?')

            print(f"\n{status_icon} {test_result['name']}: {test_result['status'].upper()}")
            if test_result['error']:
                print(f"  错误: {test_result['error']}")
            if test_result['details']:
                for detail in test_result['details'][:3]:
                    print(f"  - {detail}")

        print("\n" + "-"*60)
        print(f"总计: {self.results['summary']['total']} | "
              f"通过: {self.results['summary']['passed']} | "
              f"失败: {self.results['summary']['failed']} | "
              f"跳过: {self.results['summary']['skipped']}")
        print(f"通过率: {self.results['summary']['pass_rate']}")
        print(f"\n结论: {self.results['conclusion']}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='SDK验证工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--sdk-path', '-s',
        required=True,
        help='SDK代码路径'
    )

    parser.add_argument(
        '--test-url', '-u',
        default=None,
        help='测试URL'
    )

    parser.add_argument(
        '--captured-data', '-c',
        default=None,
        help='抓包数据路径（用于签名对比）'
    )

    parser.add_argument(
        '--output', '-o',
        default=None,
        help='输出结果文件路径'
    )

    args = parser.parse_args()

    # 创建验证器
    validator = SDKValidator(
        sdk_path=args.sdk_path,
        test_url=args.test_url,
        captured_data=args.captured_data
    )

    # 运行测试
    results = validator.run_all_tests()

    # 输出报告
    validator.print_report()

    # 保存结果
    if args.output:
        validator.save_results(args.output)
    else:
        # 默认保存到SDK目录
        default_output = os.path.join(args.sdk_path, '..', '..', 'validation', 'test-results.json')
        os.makedirs(os.path.dirname(default_output), exist_ok=True)
        validator.save_results(default_output)


if __name__ == '__main__':
    main()