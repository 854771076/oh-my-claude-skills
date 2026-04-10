#!/usr/bin/env python3
"""
APK逆向SDK生成器 - 加密参数检测脚本
检测APK中的加密算法和加密参数
"""

import argparse
import json
import sys
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 加密算法特征库
CRYPTO_SIGNATURES = {
    "MD5": {
        "patterns": ["md5", "MD5", "MessageDigest", "MD5Digest"],
        "classes": ["java.security.MessageDigest", "org.apache.commons.codec.digest.DigestUtils"],
        "output_length": [32, 16],
    },
    "SHA1": {
        "patterns": ["sha1", "SHA1", "SHA-1", "SHA1Digest"],
        "classes": ["java.security.MessageDigest"],
        "output_length": [40, 20],
    },
    "SHA256": {
        "patterns": ["sha256", "SHA256", "SHA-256", "SHA256Digest"],
        "classes": ["java.security.MessageDigest"],
        "output_length": [64, 32],
    },
    "AES": {
        "patterns": ["aes", "AES", "AESCoder", "AESCipher"],
        "classes": ["javax.crypto.Cipher", "javax.crypto.spec.AESKeySpec"],
        "key_sizes": [16, 24, 32],
    },
    "DES": {
        "patterns": ["des", "DES", "DESCoder", "DESCipher"],
        "classes": ["javax.crypto.Cipher", "javax.crypto.spec.DESKeySpec"],
        "key_sizes": [8],
    },
    "RSA": {
        "patterns": ["rsa", "RSA", "RSACoder", "RSACipher"],
        "classes": ["java.security.KeyPairGenerator", "javax.crypto.Cipher"],
    },
    "Base64": {
        "patterns": ["base64", "Base64", "B64", "encodeBase64"],
        "classes": ["java.util.Base64", "org.apache.commons.codec.binary.Base64"],
        "operation": "encode/decode",
    },
    "HMAC": {
        "patterns": ["hmac", "HMAC", "HmacSHA256", "HmacMD5"],
        "classes": ["javax.crypto.Mac"],
    },
}

# 加密关键词
CRYPTO_KEYWORDS = [
    "encrypt", "decrypt", "sign", "signature", "cipher", "crypto",
    "secret", "key", "password", "token", "md5", "sha", "aes", "des", "rsa",
    "base64", "encode", "decode", "hash", "digest", "salt"
]

# API签名参数常见名称
SIGN_PARAMS = ["sign", "signature", "token", "auth", "md5", "sig", "checksum", "hash"]


def find_crypto_classes(decompiled_dir: str) -> List[Dict]:
    """搜索加密相关类"""
    results = []
    decompiled_path = Path(decompiled_dir)
    sources_path = decompiled_path / "sources"

    if not sources_path.exists():
        return results

    for java_file in sources_path.rglob("*.java"):
        try:
            content = java_file.read_text(encoding="utf-8", errors="ignore")
            relative_path = java_file.relative_to(sources_path)

            # 检查加密算法特征
            for algo_name, signatures in CRYPTO_SIGNATURES.items():
                for pattern in signatures.get("patterns", []):
                    if pattern.lower() in content.lower():
                        # 提取相关代码片段
                        matches = []
                        for line_num, line in enumerate(content.split('\n'), 1):
                            if pattern.lower() in line.lower():
                                matches.append({
                                    "line": line_num,
                                    "code": line.strip(),
                                })

                        if matches:
                            results.append({
                                "algorithm": algo_name,
                                "file": str(relative_path),
                                "matches": matches[:10],  # 只保留前10个匹配
                                "confidence": 80 if algo_name in ["MD5", "SHA256", "AES", "Base64"] else 60,
                            })
                        break

        except Exception as e:
            pass

    return results


def find_sign_logic(decompiled_dir: str) -> List[Dict]:
    """搜索API签名逻辑"""
    results = []
    decompiled_path = Path(decompiled_dir)
    sources_path = decompiled_path / "sources"

    if not sources_path.exists():
        return results

    # 搜索包含sign参数的HTTP请求代码
    for java_file in sources_path.rglob("*.java"):
        try:
            content = java_file.read_text(encoding="utf-8", errors="ignore")
            relative_path = java_file.relative_to(sources_path)

            # 检查是否包含签名参数名
            for param in SIGN_PARAMS:
                if re.search(rf'"{param}"|\'{param}\'|{param}\s*=', content, re.IGNORECASE):
                    # 提取相关代码
                    matches = []
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if param.lower() in line.lower():
                            matches.append({
                                "line": line_num,
                                "code": line.strip(),
                            })

                    if matches:
                        results.append({
                            "param_name": param,
                            "file": str(relative_path),
                            "matches": matches[:10],
                        })
                    break

        except Exception as e:
            pass

    return results


def find_http_interceptors(decompiled_dir: str) -> List[Dict]:
    """搜索HTTP拦截器/请求处理类"""
    results = []
    decompiled_path = Path(decompiled_dir)
    sources_path = decompiled_path / "sources"

    if not sources_path.exists():
        return results

    # HTTP客户端类名模式
    http_patterns = [
        "Interceptor", "HttpClient", "OkHttp", "Retrofit", "Request",
        "HttpURLConnection", "AsyncHttpClient", "Volley"
    ]

    for java_file in sources_path.rglob("*.java"):
        try:
            content = java_file.read_text(encoding="utf-8", errors="ignore")
            relative_path = java_file.relative_to(sources_path)

            for pattern in http_patterns:
                if pattern.lower() in str(relative_path).lower() or pattern.lower() in content.lower():
                    # 检查是否有添加header/sign的逻辑
                    if re.search(r'addHeader|header\(|put\(|sign|encrypt', content, re.IGNORECASE):
                        results.append({
                            "type": "http_handler",
                            "file": str(relative_path),
                            "pattern_matched": pattern,
                        })
                        break

        except Exception as e:
            pass

    return results


def analyze_crypto(decompiled_dir: str) -> Dict:
    """综合分析加密参数"""
    result = {
        "crypto_classes": [],
        "sign_logic": [],
        "http_interceptors": [],
        "encryption_detected": False,
        "algorithms": [],
        "recommendation": None,
    }

    # 搜索加密类
    crypto_classes = find_crypto_classes(decompiled_dir)
    result["crypto_classes"] = crypto_classes

    # 提取发现的算法
    algorithms = set()
    for item in crypto_classes:
        algorithms.add(item["algorithm"])
    result["algorithms"] = list(algorithms)

    # 搜索签名逻辑
    sign_logic = find_sign_logic(decompiled_dir)
    result["sign_logic"] = sign_logic

    # 搜索HTTP拦截器
    http_interceptors = find_http_interceptors(decompiled_dir)
    result["http_interceptors"] = http_interceptors

    # 判断是否存在加密
    if crypto_classes or sign_logic:
        result["encryption_detected"] = True
        result["recommendation"] = "检测到加密逻辑,建议使用Frida Hook进行动态调试"
    else:
        result["recommendation"] = "未检测到明显加密逻辑,可直接生成SDK"

    return result


def main():
    parser = argparse.ArgumentParser(description="APK加密参数检测工具")
    parser.add_argument("--decompiled", required=True, help="反编译目录路径")
    parser.add_argument("--output", default="crypto-analysis.json", help="输出文件路径")

    args = parser.parse_args()

    # 验证目录存在
    if not Path(args.decompiled).exists():
        print(f"错误: 反编译目录不存在: {args.decompiled}")
        sys.exit(1)

    # 执行分析
    result = analyze_crypto(args.decompiled)

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