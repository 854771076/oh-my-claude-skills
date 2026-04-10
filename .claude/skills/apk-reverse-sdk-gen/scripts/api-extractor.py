#!/usr/bin/env python3
"""
APK逆向SDK生成器 - API接口提取脚本
从反编译代码中提取HTTP API接口信息
"""

import argparse
import json
import sys
import re
import os
from pathlib import Path
from typing import Dict, List, Optional

# URL匹配模式
URL_PATTERNS = [
    r'https?://[^\s"\'<>]+',
    r'baseUrl\s*=\s*["\']([^"\']+)["\']',
    r'BASE_URL\s*=\s*["\']([^"\']+)["\']',
    r'API_URL\s*=\s*["\']([^"\']+)["\']',
    r'@Url\s*\(["\']([^"\']+)["\']\)',
]

# Retrofit注解模式
RETROFIT_PATTERNS = [
    r'@GET\s*\(["\']([^"\']+)["\']\)',
    r'@POST\s*\(["\']([^"\']+)["\']\)',
    r'@PUT\s*\(["\']([^"\']+)["\']\)',
    r'@DELETE\s*\(["\']([^"\']+)["\']\)',
    r'@PATCH\s*\(["\']([^"\']+)["\']\)',
]

# 常见API路径模式
API_PATH_PATTERNS = [
    r'/api/v\d+/[^\s"\'<>]+',
    r'/v\d+/[^\s"\'<>]+',
    r'/[a-zA-Z]+/[a-zA-Z]+',
]


def extract_base_urls(decompiled_dir: str) -> List[str]:
    """提取基础URL"""
    urls = []
    decompiled_path = Path(decompiled_dir)
    sources_path = decompiled_path / "sources"

    if not sources_path.exists():
        return urls

    for java_file in sources_path.rglob("*.java"):
        try:
            content = java_file.read_text(encoding="utf-8", errors="ignore")

            # 搜索URL常量
            for pattern in URL_PATTERNS[:4]:  # 基础URL模式
                matches = re.findall(pattern, content)
                for match in matches:
                    if match.startswith("http") and match not in urls:
                        urls.append(match)

        except Exception as e:
            pass

    return urls


def extract_api_endpoints(decompiled_dir: str) -> List[Dict]:
    """提取API端点"""
    endpoints = []
    decompiled_path = Path(decompiled_dir)
    sources_path = decompiled_path / "sources"

    if not sources_path.exists():
        return endpoints

    for java_file in sources_path.rglob("*.java"):
        try:
            content = java_file.read_text(encoding="utf-8", errors="ignore")
            relative_path = java_file.relative_to(sources_path)

            # 搜索Retrofit注解
            for method_idx, pattern in enumerate(RETROFIT_PATTERNS):
                method = ["GET", "POST", "PUT", "DELETE", "PATCH"][method_idx]
                matches = re.findall(pattern, content)
                for match in matches:
                    endpoints.append({
                        "method": method,
                        "path": match,
                        "file": str(relative_path),
                        "type": "retrofit",
                    })

            # 搜索通用URL模式
            for pattern in URL_PATTERNS[0]:  # http://模式
                matches = re.findall(pattern, content)
                for match in matches:
                    if match.startswith("http") and not any(e["path"] == match for e in endpoints):
                        # 判断方法
                        method = "GET"
                        if "post" in content.lower()[:500] or "POST" in content[:500]:
                            method = "POST"
                        endpoints.append({
                            "method": method,
                            "path": match,
                            "file": str(relative_path),
                            "type": "direct_url",
                        })

        except Exception as e:
            pass

    return endpoints


def extract_request_params(decompiled_dir: str) -> List[Dict]:
    """提取请求参数结构"""
    params_list = []
    decompiled_path = Path(decompiled_dir)
    sources_path = decompiled_path / "sources"

    if not sources_path.exists():
        return params_list

    # 搜索请求类/参数类
    param_patterns = [
        r'class\s+(\w*Request\w*)',
        r'class\s+(\w*Param\w*)',
        r'class\s+(\w*Body\w*)',
        r'class\s+(\w*Dto\w*)',
    ]

    for java_file in sources_path.rglob("*.java"):
        try:
            content = java_file.read_text(encoding="utf-8", errors="ignore")
            relative_path = java_file.relative_to(sources_path)

            for pattern in param_patterns:
                matches = re.findall(pattern, content)
                for class_name in matches:
                    # 提取字段
                    fields = []
                    field_pattern = r'(private|public)\s+\w+\s+(\w+)\s*[;=]'
                    field_matches = re.findall(field_pattern, content)
                    for _, field_name in field_matches:
                        fields.append(field_name)

                    if fields:
                        params_list.append({
                            "class_name": class_name,
                            "fields": fields,
                            "file": str(relative_path),
                        })

        except Exception as e:
            pass

    return params_list


def analyze_api(decompiled_dir: str) -> Dict:
    """综合分析API接口"""
    result = {
        "base_urls": [],
        "endpoints": [],
        "request_params": [],
        "api_count": 0,
        "recommendation": None,
    }

    # 提取基础URL
    base_urls = extract_base_urls(decompiled_dir)
    result["base_urls"] = base_urls

    # 提取API端点
    endpoints = extract_api_endpoints(decompiled_dir)
    result["endpoints"] = endpoints
    result["api_count"] = len(endpoints)

    # 提取请求参数
    request_params = extract_request_params(decompiled_dir)
    result["request_params"] = request_params

    # 生成建议
    if endpoints:
        result["recommendation"] = f"发现{len(endpoints)}个API接口,建议结合加密分析生成完整SDK"
    else:
        result["recommendation"] = "未发现明确的API接口定义,可能需要动态抓包分析"

    return result


def main():
    parser = argparse.ArgumentParser(description="APK API接口提取工具")
    parser.add_argument("--decompiled", required=True, help="反编译目录路径")
    parser.add_argument("--output", default="api-list.json", help="输出文件路径")

    args = parser.parse_args()

    # 验证目录存在
    if not Path(args.decompiled).exists():
        print(f"错误: 反编译目录不存在: {args.decompiled}")
        sys.exit(1)

    # 执行分析
    result = analyze_api(args.decompiled)

    # 输出结果
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 保存结果
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {args.output}")

    sys.exit(0)


if __name__ == "__main__":
    main()