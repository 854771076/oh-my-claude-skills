#!/usr/bin/env python3
"""
页面类型检测脚本
综合判断URL对应的页面类型：static/dynamic/ajax-api

使用方式:
python page-type-detector.py <URL>

输出:
JSON格式的检测结果，包含页面类型、判断依据、建议处理流程
"""

import sys
import json
import re
from urllib.parse import urlparse, parse_qs
import requests
from typing import Dict, List, Tuple

class PageTypeDetector:
    """页面类型综合检测器"""

    # 动态页面URL扩展名特征
    DYNAMIC_EXTENSIONS = ['.php', '.jsp', '.aspx', '.do', '.action', '.py', '.rb']

    # 静态页面扩展名
    STATIC_EXTENSIONS = ['.html', '.htm', '.shtml', '.xml', '.json', '.txt']

    # API路径特征
    API_PATH_PATTERNS = ['/api/', '/v1/', '/v2/', '/rest/', '/graphql', '/service/']

    # 动态渲染HTML特征
    DYNAMIC_HTML_SIGNATURES = [
        '__NEXT_DATA__',           # Next.js
        'window.__INITIAL_STATE__', # React SSR
        'ng-version',              # Angular
        'data-v-',                 # Vue
        'webpackJsonp',            # Webpack
        '__PRELOADED_STATE__',     # Redux SSR
    ]

    # AJAX请求头特征
    AJAX_HEADERS = [
        'X-Requested-With',
        'X-API-Key',
        'Authorization',
        'X-Token',
    ]

    def __init__(self, url: str):
        self.url = url
        self.parsed_url = urlparse(url)
        self.result = {
            'url': url,
            'page_type': None,
            'confidence': 0.0,
            'evidence': [],
            'recommendation': None,
        }

    def detect(self) -> Dict:
        """执行综合检测"""
        scores = {
            'static': 0,
            'dynamic': 0,
            'ajax-api': 0,
        }

        # 1. URL结构分析
        url_score, url_evidence = self._analyze_url_structure()
        for k, v in url_score.items():
            scores[k] += v
        self.result['evidence'].extend(url_evidence)

        # 2. HTTP响应头分析
        try:
            header_score, header_evidence = self._analyze_response_headers()
            for k, v in header_score.items():
                scores[k] += v
            self.result['evidence'].extend(header_evidence)
        except Exception as e:
            self.result['evidence'].append({
                'type': 'header_check',
                'status': 'failed',
                'message': str(e)
            })

        # 3. HTML内容特征分析
        try:
            html_score, html_evidence = self._analyze_html_content()
            for k, v in html_score.items():
                scores[k] += v
            self.result['evidence'].extend(html_evidence)
        except Exception as e:
            self.result['evidence'].append({
                'type': 'html_check',
                'status': 'failed',
                'message': str(e)
            })

        # 4. 综合判定
        self._make_final_decision(scores)

        return self.result

    def _analyze_url_structure(self) -> Tuple[Dict, List]:
        """分析URL结构特征"""
        scores = {'static': 0, 'dynamic': 0, 'ajax-api': 0}
        evidence = []

        path = self.parsed_url.path.lower()
        query = self.parsed_url.query
        hostname = self.parsed_url.hostname or ''

        # 扩展名检查
        for ext in self.DYNAMIC_EXTENSIONS:
            if path.endswith(ext):
                scores['dynamic'] += 2
                evidence.append({
                    'type': 'url_extension',
                    'value': ext,
                    'indicates': 'dynamic'
                })

        for ext in self.STATIC_EXTENSIONS:
            if path.endswith(ext):
                scores['static'] += 2
                evidence.append({
                    'type': 'url_extension',
                    'value': ext,
                    'indicates': 'static'
                })

        # API路径特征
        for pattern in self.API_PATH_PATTERNS:
            if pattern in path:
                scores['ajax-api'] += 3
                evidence.append({
                    'type': 'api_path_pattern',
                    'value': pattern,
                    'indicates': 'ajax-api'
                })

        # 查询参数复杂度
        if query:
            params = parse_qs(query)
            param_count = len(params)

            # 参数数量多，倾向于动态
            if param_count > 3:
                scores['dynamic'] += 1
                evidence.append({
                    'type': 'query_params_count',
                    'value': param_count,
                    'indicates': 'dynamic'
                })

            # 检查是否有分页、过滤等典型API参数
            api_param_patterns = ['page', 'limit', 'offset', 'sort', 'filter', 'id', 'q']
            has_api_params = any(p in params for p in api_param_patterns)
            if has_api_params:
                scores['ajax-api'] += 1
                evidence.append({
                    'type': 'api_params',
                    'value': [p for p in api_param_patterns if p in params],
                    'indicates': 'ajax-api'
                })

        # 域名特征（如 api.example.com）
        if 'api' in hostname or 'service' in hostname:
            scores['ajax-api'] += 2
            evidence.append({
                'type': 'hostname',
                'value': hostname,
                'indicates': 'ajax-api'
            })

        return scores, evidence

    def _analyze_response_headers(self) -> Tuple[Dict, List]:
        """分析HTTP响应头"""
        scores = {'static': 0, 'dynamic': 0, 'ajax-api': 0}
        evidence = []

        try:
            response = requests.head(self.url, timeout=10, allow_redirects=True)
            headers = response.headers

            # Content-Type检查
            content_type = headers.get('Content-Type', '').lower()
            if 'application/json' in content_type:
                scores['ajax-api'] += 3
                evidence.append({
                    'type': 'content_type',
                    'value': content_type,
                    'indicates': 'ajax-api'
                })
            elif 'text/html' in content_type:
                scores['dynamic'] += 1  # HTML可能是动态渲染
                evidence.append({
                    'type': 'content_type',
                    'value': content_type,
                    'indicates': 'dynamic_or_static'
                })

            # Cache-Control检查
            cache_control = headers.get('Cache-Control', '')
            if 'no-cache' in cache_control or 'no-store' in cache_control:
                scores['dynamic'] += 1
                evidence.append({
                    'type': 'cache_control',
                    'value': cache_control,
                    'indicates': 'dynamic'
                })
            elif 'max-age' in cache_control:
                scores['static'] += 1
                evidence.append({
                    'type': 'cache_control',
                    'value': cache_control,
                    'indicates': 'static'
                })

            # 检查AJAX相关请求头
            for header in self.AJAX_HEADERS:
                if header.lower() in [h.lower() for h in headers.keys()]:
                    scores['ajax-api'] += 1
                    evidence.append({
                        'type': 'ajax_header',
                        'value': header,
                        'indicates': 'ajax-api'
                    })

            # Server信息
            server = headers.get('Server', '').lower()
            if any(s in server for s in ['nginx', 'apache']):
                scores['static'] += 0.5
            elif any(s in server for s in ['tomcat', 'iis', 'php']):
                scores['dynamic'] += 0.5

        except requests.RequestException as e:
            raise e

        return scores, evidence

    def _analyze_html_content(self) -> Tuple[Dict, List]:
        """分析HTML内容特征"""
        scores = {'static': 0, 'dynamic': 0, 'ajax-api': 0}
        evidence = []

        try:
            response = requests.get(self.url, timeout=15)
            html_content = response.text

            # 检查动态框架签名
            for signature in self.DYNAMIC_HTML_SIGNATURES:
                if signature in html_content:
                    scores['dynamic'] += 2
                    evidence.append({
                        'type': 'framework_signature',
                        'value': signature,
                        'indicates': 'dynamic'
                    })

            # 检查<script>标签数量
            script_count = len(re.findall(r'<script', html_content))
            if script_count > 5:
                scores['dynamic'] += 1
                evidence.append({
                    'type': 'script_count',
                    'value': script_count,
                    'indicates': 'dynamic'
                })

            # 检查内联JavaScript
            inline_js_patterns = [
                r'window\.__',
                r'data\s*=\s*\{',
                r'fetch\(',
                r'axios\.',
                r'\$\.ajax',
                r'XMLHttpRequest',
            ]
            for pattern in inline_js_patterns:
                if re.search(pattern, html_content):
                    scores['dynamic'] += 0.5
                    evidence.append({
                        'type': 'inline_js_pattern',
                        'value': pattern,
                        'indicates': 'dynamic'
                    })

            # 检查是否为纯JSON响应
            try:
                json.loads(html_content)
                scores['ajax-api'] += 3
                evidence.append({
                    'type': 'json_response',
                    'indicates': 'ajax-api'
                })
            except json.JSONDecodeError:
                pass

        except requests.RequestException as e:
            raise e

        return scores, evidence

    def _make_final_decision(self, scores: Dict):
        """做出最终判定"""
        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]
        total_score = sum(scores.values())

        if total_score == 0:
            # 无法判断时默认动态
            self.result['page_type'] = 'dynamic'
            self.result['confidence'] = 0.3
            self.result['recommendation'] = 'use_playwright_capture'
        else:
            self.result['page_type'] = max_type
            self.result['confidence'] = max_score / total_score

            # 设置处理建议
            if max_type == 'static':
                self.result['recommendation'] = 'static_parser_workflow'
            elif max_type == 'ajax-api':
                self.result['recommendation'] = 'api_sdk_generation'
            else:
                self.result['recommendation'] = 'use_playwright_capture'

        # 添加评分详情
        self.result['scores'] = scores


def main():
    if len(sys.argv) < 2:
        print("Usage: python page-type-detector.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    detector = PageTypeDetector(url)
    result = detector.detect()

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()