#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JS代码搜索与分析工具
在JS文件中搜索关键词、提取函数、分析Webpack模块

改进:
- 支持从JSON数据源(js-files.json)分析JS URL列表
- 支持下载JS内容进行深度分析
- 支持仅分析URL模式(不需要下载)
- 修复Windows终端编码问题

使用方式:
# 搜索关键词(本地文件)
python js-search-tool.py --js-dir "./capture-data/js/" --keywords "encrypt,sign,md5"

# 从JSON数据源分析JS URL
python js-search-tool.py --js-json "./capture-output/js-files.json" --analyze-urls

# 从JSON数据源下载并分析JS内容
python js-search-tool.py --js-json "./capture-output/js-files.json" --download --keywords "encrypt,sign"

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
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from urllib.parse import urlparse

# 设置标准输出编码（解决Windows终端乱码）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


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

    def __init__(self, js_dir: str = None, js_json: str = None):
        """
        初始化

        Args:
            js_dir: JS文件目录(本地文件)
            js_json: JS文件列表JSON(js-files.json格式)
        """
        self.js_dir = Path(js_dir) if js_dir else None
        self.js_json = js_json
        self.js_files = []
        self.js_urls = []  # 从JSON提取的URL列表
        self.downloaded_contents = {}  # 下载的JS内容缓存
        self.results = {
            'search_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'js_dir': str(js_dir) if js_dir else None,
            'js_json': js_json,
            'total_files': 0,
            'total_urls': 0,
            'total_size': 0,
            'keyword_matches': {},
            'function_extractions': {},
            'webpack_modules': [],
            'suspicious_functions': [],
            'url_analysis': {},  # URL分析结果
            'download_errors': []
        }

    def _load_js_files(self):
        """加载所有JS文件"""
        if self.js_dir and self.js_dir.exists():
            # 支持多种扩展名
            extensions = ['.js', '.mjs', '.cjs', '.ts', '.jsx', '.tsx']
            for ext in extensions:
                self.js_files.extend(self.js_dir.glob(f'*{ext}'))
                self.js_files.extend(self.js_dir.glob(f'**/*{ext}'))

            self.results['total_files'] = len(self.js_files)
            self.results['total_size'] = sum(f.stat().st_size for f in self.js_files if f.exists())
        elif self.js_dir and not self.js_dir.exists():
            raise FileNotFoundError(f"JS目录不存在: {self.js_dir}")

    def _load_js_urls_from_json(self):
        """从JSON文件加载JS URL列表"""
        if not self.js_json or not os.path.exists(self.js_json):
            raise FileNotFoundError(f"JS JSON文件不存在: {self.js_json}")

        with open(self.js_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 支持两种JSON格式：
        # 1. 直接URL列表: ["url1", "url2", ...]
        # 2. 请求对象列表: [{"url": "url1", ...}, ...]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    self.js_urls.append({'url': item, 'method': 'GET'})
                elif isinstance(item, dict) and 'url' in item:
                    self.js_urls.append({
                        'url': item.get('url', ''),
                        'method': item.get('method', 'GET'),
                        'headers': item.get('headers', {}),
                        'postData': item.get('postData'),
                        'response': item.get('response', {})
                    })

        self.results['total_urls'] = len(self.js_urls)
        print(f"[INFO] 从JSON加载了 {len(self.js_urls)} 个JS URL")

    def _download_js_content(self, max_files: int = 50, timeout: int = 30):
        """
        下载JS内容

        Args:
            max_files: 最大下载文件数
            timeout: 请求超时时间(秒)
        """
        print(f"[INFO] 开始下载JS内容(最多{max_files}个文件)...")

        # 过滤有效的HTTP/HTTPS URL
        valid_urls = [
            u for u in self.js_urls
            if u['url'].startswith('http://') or u['url'].startswith('https://')
        ]

        # 跳过 chrome:// 等特殊URL
        valid_urls = [u for u in valid_urls if not u['url'].startswith('chrome://')]

        downloaded_count = 0
        for url_info in valid_urls[:max_files]:
            url = url_info['url']
            try:
                headers = url_info.get('headers', {})
                # 移除可能导致问题的头
                clean_headers = {k: v for k, v in headers.items()
                                if k.lower() not in ['host', 'content-length', 'accept-encoding']}

                resp = requests.get(url, headers=clean_headers, timeout=timeout)
                if resp.status_code == 200:
                    self.downloaded_contents[url] = resp.text
                    downloaded_count += 1
                    print(f"[DOWNLOADED] {url[:80]}... ({len(resp.text)} bytes)")
            except Exception as e:
                self.results['download_errors'].append({
                    'url': url,
                    'error': str(e)
                })
                print(f"[ERROR] 下载失败 {url[:50]}...: {e}")

        print(f"[INFO] 成功下载 {downloaded_count}/{min(len(valid_urls), max_files)} 个JS文件")
        self.results['downloaded_count'] = downloaded_count

    def analyze_urls(self) -> Dict:
        """
        分析JS URL模式(不下载内容)

        Returns:
            URL分析结果
        """
        self._load_js_urls_from_json()

        url_patterns = {
            'webpack': [],
            'minified': [],
            'chunk': [],
            'vendor': [],
            'lib': [],
            'components': [],
            'app': [],
            'main': [],
            'other': []
        }

        for url_info in self.js_urls:
            url = url_info['url']
            filename = urlparse(url).path.split('/')[-1] or url

            # 分类URL
            if 'webpack' in filename.lower() or 'webpack' in url.lower():
                url_patterns['webpack'].append(url)
            elif '.min.' in filename or '-min.' in filename:
                url_patterns['minified'].append(url)
            elif 'chunk' in filename.lower():
                url_patterns['chunk'].append(url)
            elif 'vendor' in filename.lower():
                url_patterns['vendor'].append(url)
            elif 'lib' in filename.lower():
                url_patterns['lib'].append(url)
            elif 'component' in filename.lower():
                url_patterns['components'].append(url)
            elif 'app' in filename.lower():
                url_patterns['app'].append(url)
            elif 'main' in filename.lower():
                url_patterns['main'].append(url)
            else:
                url_patterns['other'].append(url)

        # 统计
        self.results['url_analysis'] = {
            'patterns': {k: len(v) for k, v in url_patterns.items()},
            'urls_by_pattern': url_patterns,
            'domains': self._extract_domains()
        }

        return self.results['url_analysis']

    def _extract_domains(self) -> Dict:
        """提取域名统计"""
        domains = {}
        for url_info in self.js_urls:
            url = url_info['url']
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                if domain:
                    domains[domain] = domains.get(domain, 0) + 1
            except:
                pass
        return dict(sorted(domains.items(), key=lambda x: x[1], reverse=True)[:20])

    def search_keywords_from_downloaded(self, keywords: List[str], context_lines: int = 3) -> Dict:
        """
        从下载的JS内容搜索关键词

        Args:
            keywords: 关键词列表
            context_lines: 上下文行数

        Returns:
            匹配结果字典
        """
        for keyword in keywords:
            self.results['keyword_matches'][keyword] = {
                'count': 0,
                'files': []
            }

        for url, content in self.downloaded_contents.items():
            lines = content.split('\n')

            for keyword in keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                matches_in_file = []

                for i, line in enumerate(lines):
                    if pattern.search(line):
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
                        'file': url,
                        'matches': matches_in_file
                    })

        return self.results['keyword_matches']

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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从JSON数据源分析JS URL(不下载)
  python js-search-tool.py --js-json "./js-files.json" --analyze-urls

  # 从JSON数据源下载并搜索关键词
  python js-search-tool.py --js-json "./js-files.json" --download --keywords "encrypt,sign"

  # 分析本地JS文件目录
  python js-search-tool.py --js-dir "./js/" --keywords "encrypt,sign"
        """
    )

    # 数据源参数
    parser.add_argument(
        '--js-dir', '-d',
        help='JS文件目录(本地文件)'
    )

    parser.add_argument(
        '--js-json', '-j',
        help='JS文件列表JSON(js-files.json格式)'
    )

    # 分析模式参数
    parser.add_argument(
        '--analyze-urls', '-a',
        action='store_true',
        help='分析JS URL模式(不下载内容)'
    )

    parser.add_argument(
        '--download', '-D',
        action='store_true',
        help='下载JS内容进行分析'
    )

    parser.add_argument(
        '--max-download', '-m',
        type=int,
        default=50,
        help='最大下载文件数(默认50)'
    )

    # 搜索参数
    parser.add_argument(
        '--keywords', '-k',
        default='encrypt,sign,md5,sha,crypto,base64',
        help='搜索关键词(逗号分隔)'
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
        help='指定要提取的函数名(逗号分隔)'
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

    # 检查数据源
    if not args.js_dir and not args.js_json:
        print("错误: 必须指定 --js-dir 或 --js-json")
        parser.print_help()
        sys.exit(1)

    # 初始化工具
    tool = JSSearchTool(js_dir=args.js_dir, js_json=args.js_json)

    # 处理关键词
    keywords = []
    if args.keyword_group:
        keywords = JSSearchTool.KEYWORD_GROUPS.get(args.keyword_group, [])
    if args.keywords:
        keywords.extend([k.strip() for k in args.keywords.split(',')])

    # 根据数据源选择分析模式
    if args.js_json:
        # JSON数据源模式
        if args.analyze_urls:
            print("[INFO] 分析JS URL模式...")
            url_analysis = tool.analyze_urls()
            print(f"\n[URL分析结果]")
            print(f"总URL数: {url_analysis['patterns']}")
            print(f"\n主要域名:")
            for domain, count in list(url_analysis['domains'].items())[:10]:
                print(f"  - {domain}: {count} 个JS文件")

        if args.download:
            print("[INFO] 下载JS内容...")
            tool._load_js_urls_from_json()
            tool._download_js_content(max_files=args.max_download)

            if keywords:
                print(f"[INFO] 搜索关键词: {keywords}")
                tool.search_keywords_from_downloaded(keywords)

            if args.extract_functions:
                print("[INFO] 从下载内容提取函数...")
                # 注意: 需要实现从下载内容提取函数的逻辑

    elif args.js_dir:
        # 本地文件模式
        if keywords:
            print(f"[INFO] 搜索关键词: {keywords}")
            tool.search_keywords(keywords)

        if args.extract_functions:
            func_names = [f.strip() for f in args.function_names.split(',')] if args.function_names else None
            print(f"[INFO] 提取函数: {func_names or '全部'}")
            tool.extract_functions(func_names)

        if args.analyze_webpack:
            print("[INFO] 分析Webpack模块...")
            tool.analyze_webpack()

    # 输出结果
    if args.output:
        tool.save_results(args.output)
    else:
        # 打印摘要报告
        print("\n" + "="*60)
        print("JS代码分析报告")
        print("="*60)
        print(f"分析时间: {tool.results['search_time']}")
        if tool.results.get('total_urls'):
            print(f"URL总数: {tool.results['total_urls']}")
            print(f"下载文件: {tool.results.get('downloaded_count', 0)}")
        if tool.results.get('total_files'):
            print(f"本地文件: {tool.results['total_files']}")
            print(f"总大小: {tool.results['total_size'] / 1024:.1f} KB")

        # 关键词匹配摘要
        if tool.results['keyword_matches']:
            print("\n关键词匹配:")
            for kw, data in tool.results['keyword_matches'].items():
                print(f"  - {kw}: {data['count']} 次匹配")

        # 可疑函数
        if tool.results['suspicious_functions']:
            print(f"\n可疑加密函数: {len(tool.results['suspicious_functions'])} 个")
            for func in tool.results['suspicious_functions'][:10]:
                print(f"  - {func['name']} ({func['file']})")

    # 输出JSON摘要
    print("\n[JSON SUMMARY]")
    summary = {
        'total_files': tool.results.get('total_files', 0),
        'total_urls': tool.results.get('total_urls', 0),
        'downloaded_count': tool.results.get('downloaded_count', 0),
        'keyword_count': {k: v['count'] for k, v in tool.results['keyword_matches'].items()},
        'suspicious_functions_count': len(tool.results['suspicious_functions']),
        'webpack_files_count': len(tool.results['webpack_modules']),
        'download_errors': len(tool.results.get('download_errors', []))
    }
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()