#!/usr/bin/env python3
"""
APK逆向SDK生成器 - SDK生成脚本
根据分析结果生成多语言SDK
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def generate_python_sdk(analysis: Dict, package_name: str, output_dir: str) -> str:
    """生成Python SDK"""
    sdk_content = '''#!/usr/bin/env python3
"""
{package_name} API SDK
自动生成于: {timestamp}

功能:
- API请求封装
- 签名算法还原
- 加密参数处理
"""

import hashlib
import hmac
import base64
import json
import time
import requests
from typing import Dict, Optional, Any
from Crypto.Cipher import AES  # pycryptodome

class {class_name}Client:
    """API客户端"""

    BASE_URL = "{base_url}"

    def __init__(self, device_id: str = None, user_agent: str = None):
        self.device_id = device_id or self._generate_device_id()
        self.user_agent = user_agent or "Android/{package_name}"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _generate_device_id(self) -> str:
        """生成设备ID"""
        import uuid
        return str(uuid.uuid4())

    def _get_timestamp(self) -> int:
        """获取时间戳"""
        return int(time.time() * 1000)

    def _sign(self, params: Dict) -> str:
        """
        签名算法
        根据逆向分析还原的签名逻辑
        """
        # 排序参数
        sorted_params = sorted(params.items())
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])

        # TODO: 根据分析结果修改签名算法
        # 当前使用示例: MD5(param_str + secret_key)
        secret_key = "your_secret_key"  # 需要从分析中获取

        sign = hashlib.md5((param_str + secret_key).encode()).hexdigest()
        return sign

    def request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        通用请求方法

        Args:
            method: GET/POST/PUT/DELETE
            endpoint: API路径
            params: 查询参数
            data: 请求体数据

        Returns:
            API响应数据
        """
        url = f"{self.BASE_URL}{endpoint}"

        # 添加签名参数
        if params:
            params = params.copy()
            params["timestamp"] = self._get_timestamp()
            params["sign"] = self._sign(params)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"不支持的方法: {method}")

            return response.json()
        except Exception as e:
            return {"error": str(e)}

    # 以下是根据API分析生成的具体方法
{api_methods}


# 使用示例
if __name__ == "__main__":
    client = {class_name}Client()
    # 示例调用
    # result = client.get_user_info(user_id="123")
    # print(result)
'''

    # 从分析数据提取信息
    base_url = analysis.get("base_urls", ["https://api.example.com"])[0]
    endpoints = analysis.get("endpoints", [])
    crypto_info = analysis.get("crypto_analysis", {})

    # 生成API方法
    api_methods = []
    for endpoint in endpoints:
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/unknown")
        method_name = path.replace("/", "_").replace("-", "_").lower()

        if method_name.startswith("_"):
            method_name = method_name[1:]

        api_methods.append(f'''
    def {method_name}(self, **kwargs):
        """{method} {path}"""
        return self.request("{method}", "{path}", params=kwargs)
''')

    # 生成类名 (PascalCase)
    class_parts = package_name.replace("-", "_").split("_")
    class_name = "".join(part.capitalize() for part in class_parts) + "Api"

    # 填充模板
    sdk_content = sdk_content.format(
        package_name=package_name,
        timestamp=datetime.now().isoformat(),
        class_name=class_name,
        base_url=base_url,
        api_methods="\n".join(api_methods),
    )

    # 写入文件
    output_path = Path(output_dir) / "python" / f"{class_name.lower()}_sdk.py"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sdk_content, encoding="utf-8")

    return str(output_path)


def generate_java_sdk(analysis: Dict, package_name: str, output_dir: str) -> str:
    """生成Java SDK"""
    sdk_content = '''package com.example.sdk;

import java.security.MessageDigest;
import java.util.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.*;

/**
 * {package_name} API SDK
 * 自动生成于: {timestamp}
 */
public class {class_name}Client {

    private static final String BASE_URL = "{base_url}";
    private String deviceId;
    private String userAgent;

    public {class_name}Client() {
        this.deviceId = generateDeviceId();
        this.userAgent = "Android/{package_name}";
    }

    private String generateDeviceId() {
        return UUID.randomUUID().toString();
    }

    private long getTimestamp() {
        return System.currentTimeMillis();
    }

    /**
     * 签名算法
     * 根据逆向分析还原
     */
    private String sign(Map<String, String> params) {
        // 排序参数
        List<String> keys = new ArrayList<>(params.keySet());
        Collections.sort(keys);

        StringBuilder sb = new StringBuilder();
        for (String key : keys) {
            sb.append(key).append("=").append(params.get(key)).append("&");
        }

        // TODO: 根据分析结果修改签名算法
        String secretKey = "your_secret_key";
        String paramStr = sb.toString();

        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest((paramStr + secretKey).getBytes());
            StringBuilder hexString = new StringBuilder();
            for (byte b : digest) {
                hexString.append(String.format("%02x", b));
            }
            return hexString.toString();
        } catch (Exception e) {
            return "";
        }
    }

    // API方法
{api_methods}
}
'''

    base_url = analysis.get("base_urls", ["https://api.example.com"])[0]
    endpoints = analysis.get("endpoints", [])
    class_name = package_name.replace(".", "_").replace("-", "_").capitalize() + "Api"

    # 生成API方法
    api_methods = []
    for endpoint in endpoints:
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/unknown")
        method_name = path.replace("/", "_").replace("-", "_").lower()
        if method_name.startswith("_"):
            method_name = method_name[1:]

        api_methods.append(f'''
    public String {method_name}(Map<String, String> params) throws Exception {{
        params.put("timestamp", String.valueOf(getTimestamp()));
        params.put("sign", sign(params));
        return request("{method}", "{path}", params);
    }}
''')

    sdk_content = sdk_content.format(
        package_name=package_name,
        timestamp=datetime.now().isoformat(),
        class_name=class_name,
        base_url=base_url,
        api_methods="\n".join(api_methods),
    )

    output_path = Path(output_dir) / "java" / f"{class_name}Client.java"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sdk_content, encoding="utf-8")

    return str(output_path)


def generate_js_sdk(analysis: Dict, package_name: str, output_dir: str) -> str:
    """生成JavaScript SDK"""
    sdk_content = '''/**
 * {package_name} API SDK
 * 自动生成于: {timestamp}
 */

const crypto = require('crypto');
const axios = require('axios');

class {class_name}Client {
    constructor(options = {}) {{
        this.baseUrl = '{base_url}';
        this.deviceId = options.deviceId || this.generateDeviceId();
        this.userAgent = options.userAgent || 'Android/{package_name}';
    }}

    generateDeviceId() {{
        return crypto.randomUUID();
    }}

    getTimestamp() {{
        return Date.now();
    }}

    /**
     * 签名算法
     * 根据逆向分析还原
     */
    sign(params) {{
        const sortedKeys = Object.keys(params).sort();
        const paramStr = sortedKeys.map(k => `${{k}}=${{params[k]}}`).join('&');

        // TODO: 根据分析结果修改签名算法
        const secretKey = 'your_secret_key';
        return crypto.createHash('md5').update(paramStr + secretKey).digest('hex');
    }}

    async request(method, endpoint, params = null, data = null) {{
        const url = `${{this.baseUrl}}${{endpoint}}`;

        if (params) {{
            params.timestamp = this.getTimestamp();
            params.sign = this.sign(params);
        }}

        try {{
            const response = await axios({{
                method,
                url,
                params,
                data,
                headers: {{
                    'User-Agent': this.userAgent,
                    'Content-Type': 'application/json'
                }}
            }});
            return response.data;
        }} catch (error) {{
            return {{ error: error.message }};
        }}
    }}

    // API方法
{api_methods}
}

module.exports = {class_name}Client;
'''

    base_url = analysis.get("base_urls", ["https://api.example.com"])[0]
    endpoints = analysis.get("endpoints", [])
    class_name = package_name.replace(".", "_").replace("-", "_").capitalize() + "Api"

    api_methods = []
    for endpoint in endpoints:
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/unknown")
        method_name = path.replace("/", "_").replace("-", "_").lower()
        if method_name.startswith("_"):
            method_name = method_name[1:]

        api_methods.append(f'''
    async {method_name}(params = null) {{
        return this.request('{method}', '{path}', params);
    }}
''')

    sdk_content = sdk_content.format(
        package_name=package_name,
        timestamp=datetime.now().isoformat(),
        class_name=class_name,
        base_url=base_url,
        api_methods="\n".join(api_methods),
    )

    output_path = Path(output_dir) / "js" / f"{class_name.toLowerCase()}_sdk.js"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sdk_content, encoding="utf-8")

    return str(output_path)


def generate_sdk(analysis_dir: str, languages: List[str], package_name: str, output_dir: str) -> Dict:
    """生成多语言SDK"""
    result = {
        "languages": languages,
        "output_files": [],
        "success": False,
    }

    # 读取分析结果
    analysis_path = Path(analysis_dir)

    # 合并所有分析文件
    analysis = {}
    for json_file in analysis_path.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            analysis.update(data)
        except:
            pass

    # 确保必要字段存在
    if not analysis.get("base_urls"):
        analysis["base_urls"] = ["https://api.example.com"]
    if not analysis.get("endpoints"):
        analysis["endpoints"] = []

    # 生成各语言SDK
    for language in languages:
        if language == "python":
            output_file = generate_python_sdk(analysis, package_name, output_dir)
            result["output_files"].append({"language": "python", "path": output_file})
        elif language == "java":
            output_file = generate_java_sdk(analysis, package_name, output_dir)
            result["output_files"].append({"language": "java", "path": output_file})
        elif language == "js":
            output_file = generate_js_sdk(analysis, package_name, output_dir)
            result["output_files"].append({"language": "js", "path": output_file})

    result["success"] = len(result["output_files"]) > 0

    return result


def main():
    parser = argparse.ArgumentParser(description="APK SDK生成工具")
    parser.add_argument("--analysis", required=True, help="分析结果目录")
    parser.add_argument("--languages", default="python", help="SDK语言(python/java/js,逗号分隔)")
    parser.add_argument("--package", required=True, help="APK包名")
    parser.add_argument("--output", default="output/sdk", help="SDK输出目录")

    args = parser.parse_args()

    languages = args.languages.split(",")
    result = generate_sdk(args.analysis, languages, args.package, args.output)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["success"]:
        print(f"\nSDK生成成功!")
        for file_info in result["output_files"]:
            print(f"  {file_info['language']}: {file_info['path']}")
    else:
        print("\nSDK生成失败")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()