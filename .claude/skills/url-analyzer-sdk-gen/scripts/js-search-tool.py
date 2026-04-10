#!/usr/bin/env python3
"""
JS代码搜索与分析工具
在JS文件中搜索关键词、提取函数、分析Webpack模块

使用方式:
# 搜索关键词
python js-search-tool.py --js-dir "./capture-data/js/" --keywords "encrypt,sign,md5"

# 提取函数
python js-search-tool.py --js-dir "./capture-data/js/" --extract-functions --function-names "getSign"

# 分析Webpack
python js-search-tool.py --js-dir "./capture-data/js/" --analyze-webpack
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class JSSearchTool:
    """JS代码搜索工具"""

    # 预定义的加密关键词组
    KEYWORD_GROUPS = {
        'crypto': ['encrypt', 'decrypt', 'cipher', 'crypto', 'CryptoJS', 'JSEncrypt'],
        'hash': ['md5', 'sha1', 'sha256', 'sha512', 'hash', 'digest', 'hex'],
        'sign': ['sign', 'signature', 'getSign', 'makeSign', 'calcSign', 'createSign'],
        'encode': ['base64', 'btoa', 'atob', 'encode', 'decode', 'encodeURIComponent'],
        'auth': ['token', 'auth', 'secret', 'key', 'apiKey', 'timestamp', 'nonce']
    }

    # 函数定义正则模式
    FUNCTION_PATTERNS = [
        r'function\s+(\w+)\s*\([^)]*\)\s*\{',  # function name() {}
        r'const\s+(\w+)\s*=\s*(?:async\s+)?function',  # const name = function
        r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',  # const name = () =>
        r'(\w+)\s*:\s*function\s*\([^)]*\)',  # name: function()
        r'(\w+)\s*\([^)]*\)\s*\{',  # name() { (可能误报)
    ]

    def __init__(self, js_dir: str):
        """
        初始化

        Args:
            js_dir: JS文件目录
        """
        self.js_dir = Path(js_dir)
        self.js_files = []
        self.results = {
            'search_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'js_dir': str(js_dir),
            'total_files': 0,
            'total_size': 0,
            'keyword_matches': {},
            'function_extractions': {},
            'webpack_modules': [],
            'suspicious_functions': []
        }

    def _load_js_files(self):
        """加载所有JS文件"""
        if not self.js_dir.exists():
            raise FileNotFoundError(f"JS目录不存在: {self.js_dir}")

        # 支持多种扩展名
        extensions = ['.js', '.mjs', '.cjs', '.ts', '.jsx', '.tsx']
        for ext in extensions:
            self.js_files.extend(self.js_dir.glob(f'*{ext}'))
            self.js_files.extend(self.js_dir.glob(f'**/*{ext}'))

        self.results['total_files'] = len(self.js_files)
        self.results['total_size'] = sum(f.stat().st_size for f in self.js_files if f.exists())

    def _read_file(self, filepath: Path) -> str:
        """读取文件内容"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"[ERROR] 读取文件失败 {filepath}: {e}")
            return ""

    def search_keywords(self, keywords: List[str], context_lines: int = 3) -> Dict:
        """
        搜索关键词

        Args:
            keywords: 关键词列表
            context_lines: 上下文行数

        Returns:
            匹配结果字典
        """
        self._load_js_files()

        for keyword in keywords:
            self.results['keyword_matches'][keyword] = {
                'count': 0,
                'files': []
            }

        for js_file in self.js_files:
            content = self._read_file(js_file)
            lines = content.split('\n')

            for keyword in keywords:
                # 不区分大小写搜索
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches_in_file = []

                for i, line in enumerate(lines):
                    if pattern.search(line):
                        # 提取上下文
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)
                        context = {
                            'line_number': i + 1,
                            'line': line.strip(),
                            'context': '\n'.join(lines[start:end])
                        }
                        matches_in_file.append(context)

                if matches_in_file:
                    self.results['keyword_matches'][keyword]['count'] += len(matches_in_file)
                    self.results['keyword_matches'][keyword]['files'].append({
                        'file': str(js_file.relative_to(self.js_dir)),
                        'matches': matches_in_file
                    })

        return self.results['keyword_matches']

    def extract_functions(self, function_names: List[str] = None, extract_all: bool = False) -> Dict:
        """
        提取函数定义

        Args:
            function_names: 指定要提取的函数名
            extract_all: 是否提取所有函数

        Returns:
            函数提取结果
        """
        self._load_js_files()

        for js_file in self.js_files:
            content = self._read_file(js_file)
            lines = content.split('\n')

            # 搜索函数定义
            for pattern in self.FUNCTION_PATTERNS:
                for match in re.finditer(pattern, content):
                    func_name = match.group(1)

                    # 过滤条件
                    if function_names and func_name not in function_names:
                        continue

                    # 提取完整函数体（简单实现）
                    start_pos = match.start()
                    brace_count = 0
                    in_function = False
                    end_pos = start_pos

                    for i, char in enumerate(content[start_pos:], start_pos):
                        if char == '{':
                            brace_count += 1
                            in_function = True
                        elif char == '}':
                            brace_count -= 1
                            if in_function and brace_count == 0:
                                end_pos = i + 1
                                break

                    func_body = content[start_pos:end_pos]

                    # 检查是否为可疑加密函数
                    is_suspicious = any(
                        kw in func_body.lower()
                        for kw in ['encrypt', 'sign', 'md5', 'sha', 'crypto', 'base64', 'key', 'secret']
                    )

                    if func_name not in self.results['function_extractions']:
                        self.results['function_extractions'][func_name] = []

                    self.results['function_extractions'][func_name].append({
                        'file': str(js_file.relative_to(self.js_dir)),
                        'body': func_body[:2000],  # 截断过长的函数
                        'full_length': len(func_body),
                        'is_suspicious': is_suspicious,
                        'line_number': content[:start_pos].count('\n') + 1
                    })

                    if is_suspicious and func_name not in [f['name'] for f in self.results['suspicious_functions']]:
                        self.results['suspicious_functions'].append({
                            'name': func_name,
                            'file': str(js_file.relative_to(self.js_dir)),
                            'reason': '包含加密相关关键词'
                        })

        return self.results['function_extractions']

    def analyze_webpack(self) -> Dict:
        """
        分析Webpack模块结构

        Returns:
            Webpack分析结果
        """
        self._load_js_files()

        webpack_signatures = [
            r'webpackJsonp',
            r'__webpack_require__',
            r'__webpack_modules__',
            r'webpackChunk',
            r'self\[["\']webpackChunk'
        ]

        for js_file in self.js_files:
            content = self._read_file(js_file)

            is_webpack = False
            for sig in webpack_signatures:
                if re.search(sig, content):
                    is_webpack = True
                    break

            if is_webpack:
                # 尝试提取模块
                modules = []

                # 模式1: webpackJsonp.push([chunkId, {...}])
                jsonp_pattern = r'webpackJsonp\.push\(\[\s*(\d+),\s*\{([^}]+)\}'
                for match in re.finditer(jsonp_pattern, content):
                    modules.append({
                        'type': 'jsonp_chunk',
                        'chunk_id': match.group(1),
                        'size': len(match.group(2))
                    })

                # 模式2: 函数调用模块
                func_pattern = r'\((\w+)\((function|[\d,]+)\)'
                for match in re.finditer(func_pattern, content[:5000]):  # 只搜索前5000字符
                    modules.append({
                        'type': 'function_module',
                        'name': match.group(1)
                    })

                self.results['webpack_modules'].append({
                    'file': str(js_file.relative_to(self.js_dir)),
                    'is_webpack': True,
                    'modules': modules[:20],  # 限制输出
                    'file_size': js_file.stat().st_size
                })

        return {'webpack_modules': self.results['webpack_modules']}

    def generate_report(self) -> str:
        """
        生成分析报告

        Returns:
            Markdown格式的报告
        """
        report = f"""# JS代码搜索分析报告

## 概述
- **分析时间**: {self.results['search_time']}
- **JS目录**: {self.results['js_dir']}
- **文件总数**: {self.results['total_files']}
- **总大小**: {self.results['total_size'] / 1024 / 1024:.2f} MB

## 关键词搜索结果

"""

        for keyword, data in self.results['keyword_matches'].items():
            report += f"### 关键词: `{keyword}`\n"
            report += f"- 匹配次数: {data['count']}\n"
            report += f"- 涉及文件: {len(data['files'])} 个\n\n"

            for file_info in data['files'][:5]:  # 只显示前5个文件
                report += f"#### 文件: {file_info['file']}\n"
                for match in file_info['matches'][:3]:  # 每个文件只显示前3个匹配
                    report += f"- 行 {match['line_number']}: `{match['line'][:100]}{'...' if len(match['line']) > 100 else ''}`\n"
                report += "\n"

        if self.results['suspicious_functions']:
            report += "## 可疑加密函数\n\n"
            for func in self.results['suspicious_functions'][:20]:
                report += f"- **{func['name']}** ({func['file']}) - {func['reason']}\n"

        if self.results['webpack_modules']:
            report += "\n## Webpack模块分析\n\n"
            for wp in self.results['webpack_modules']:
                report += f"- **{wp['file']}** ({wp['file_size'] / 1024:.1f} KB)\n"

        return report

    def save_results(self, output_path: str):
        """保存结果到JSON文件"""
        # 清理不能JSON序列化的数据
        clean_results = {
            'search_time': self.results['search_time'],
            'js_dir': self.results['js_dir'],
            'total_files': self.results['total_files'],
            'total_size': self.results['total_size'],
            'keyword_matches': {},
            'suspicious_functions': self.results['suspicious_functions'],
            'webpack_modules': self.results['webpack_modules']
        }

        # 简化keyword_matches
        for keyword, data in self.results['keyword_matches'].items():
            clean_results['keyword_matches'][keyword] = {
                'count': data['count'],
                'file_count': len(data['files'])
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, indent=2, ensure_ascii=False)

        print(f"[SAVED] 结果已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='JS代码搜索与分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--js-dir', '-d',
        required=True,
        help='JS文件目录'
    )

    parser.add_argument(
        '--keywords', '-k',
        default='encrypt,sign,md5,sha,crypto,base64',
        help='搜索关键词（逗号分隔）'
    )

    parser.add_argument(
        '--keyword-group', '-g',
        choices=['crypto', 'hash', 'sign', 'encode', 'auth'],
        help='使用预定义关键词组'
    )

    parser.add_argument(
        '--extract-functions', '-e',
        action='store_true',
        help='提取函数定义'
    )

    parser.add_argument(
        '--function-names', '-f',
        help='指定要提取的函数名（逗号分隔）'
    )

    parser.add_argument(
        '--analyze-webpack', '-w',
        action='store_true',
        help='分析Webpack模块'
    )

    parser.add_argument(
        '--output', '-o',
        default=None,
        help='输出文件路径'
    )

    args = parser.parse_args()

    # 初始化工具
    tool = JSSearchTool(args.js_dir)

    # 处理关键词
    keywords = []
    if args.keyword_group:
        keywords = JSSearchTool.KEYWORD_GROUPS.get(args.keyword_group, [])
    if args.keywords:
        keywords.extend([k.strip() for k in args.keywords.split(',')])

    # 执行搜索
    if keywords:
        print(f"[INFO] 搜索关键词: {keywords}")
        tool.search_keywords(keywords)

    # 提取函数
    if args.extract_functions:
        func_names = [f.strip() for f in args.function_names.split(',')] if args.function_names else None
        print(f"[INFO] 提取函数: {func_names or '全部'}")
        tool.extract_functions(func_names)

    # 分析Webpack
    if args.analyze_webpack:
        print("[INFO] 分析Webpack模块...")
        tool.analyze_webpack()

    # 输出结果
    if args.output:
        tool.save_results(args.output)
    else:
        # 打印报告
        print("\n" + "="*60)
        print(tool.generate_report())

    # 输出JSON结果
    print("\n[JSON SUMMARY]")
    summary = {
        'total_files': tool.results['total_files'],
        'keyword_count': {k: v['count'] for k, v in tool.results['keyword_matches'].items()},
        'suspicious_functions_count': len(tool.results['suspicious_functions']),
        'webpack_files_count': len(tool.results['webpack_modules'])
    }
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()