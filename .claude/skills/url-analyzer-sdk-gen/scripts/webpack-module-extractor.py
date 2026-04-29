#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webpack模块提取工具 V1.0
从打包的JS文件中定位并提取包含密钥的模块

==== 背景说明 ====
在福建省公共资源交易平台逆向中发现：
1. 加密函数通过 n("moduleId") 导入依赖
2. function b(t) { var e = h.a.enc.Utf8.parse(r["e"]), ... }
3. r = n("a078") 包含所有密钥: r["e"], r["i"], r["a"]

因此，关键是追踪依赖链找到真正的密钥模块！

==== 使用方法 ====
# 1. 先找到加密函数的位置（通常在包含 portal-sign 的模块）
python webpack-module-extractor.py app.js --find-sign-func

# 2. 提取加密函数模块，分析依赖
python webpack-module-extractor.py app.js --extract-module "b775"

# 3. 追踪依赖中的密钥模块（如 r = n("a078")）
python webpack-module-extractor.py app.js --extract-module "a078"

# 4. 直接搜索所有导出密钥的模块
python webpack-module-extractor.py app.js --find-keys
"""

import re
import json
import argparse
import sys
from typing import Dict, List, Optional, Tuple, Any
from collections import OrderedDict

# 解决Windows终端编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


class WebpackModuleExtractor:
    """Webpack模块提取器"""

    # 常见的模块定义模式
    MODULE_PATTERNS = [
        # "moduleId":function(...)
        r'"([0-9a-fA-F]{3,10})":function\(',
        # moduleId:function(...)
        r'([0-9a-fA-F]{3,10}):function\(',
    ]

    # 依赖导入模式（关键！）
    DEPENDENCY_PATTERNS = [
        r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*n\s*\(\s*"([0-9a-fA-F]+)"\s*\)',  # var a = n("abc12")
        r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*n\s*\(\s*\'([0-9a-fA-F]+)\'\s*\)',  # var a = n('abc12')
        r'var\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*n\s*\(\s*"([^"]+)"\s*\)',  # var a = n("123")
        r'let\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*n\s*\(\s*"([^"]+)"\s*\)',
        r'const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*n\s*\(\s*"([^"]+)"\s*\)',
    ]

    # 密钥导出模式
    KEY_EXPORT_PATTERNS = [
        r'n\.d\(e,\s*["\'](e)["\']',   # n.d(e, "e", ...)
        r'n\.d\(e,\s*["\'](i)["\']',   # n.d(e, "i", ...)
        r'n\.d\(e,\s*["\'](a)["\']',   # n.d(e, "a", ...)
        r'n\.d\(e,\s*["\'](s)["\']',   # n.d(e, "s", ...)
        r'n\.d\(e,\s*["\']([a-z])["\']',  # 单个字符的导出
    ]

    # 密钥字符串值模式
    KEY_VALUE_PATTERNS = [
        r'["\']([A-Z0-9]{16})["\']',  # AES IV (16 chars)
        r'["\']([A-Z0-9]{32})["\']',  # AES Key (32 chars) / MD5 Salt
        r'["\']([A-Z0-9]{16,64})["\']',  # 通用密钥
    ]

    def __init__(self, js_file: str):
        self.js_file = js_file
        self.content = self._load_js()
        self.modules: Dict[str, dict] = {}
        self.key_modules: List[dict] = []
        self.dependencies: Dict[str, List[str]] = {}

    def _load_js(self) -> str:
        """加载JS文件"""
        try:
            with open(self.js_file, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"[ERROR] 无法加载文件 {self.js_file}: {e}")
            sys.exit(1)

    def find_all_modules(self) -> Dict[str, int]:
        """查找文件中所有模块ID及其位置"""
        found_modules = {}

        for pattern in self.MODULE_PATTERNS:
            for match in re.finditer(pattern, self.content):
                module_id = match.group(1)
                position = match.start()
                # 避免重复
                if module_id not in found_modules or position < found_modules[module_id]:
                    found_modules[module_id] = position

        print(f"[INFO] 找到 {len(found_modules)} 个模块ID")
        return found_modules

    def extract_module_content(self, module_id: str, max_length: int = 10000) -> Optional[str]:
        """
        提取单个模块的内容

        Args:
            module_id: 模块ID
            max_length: 最大提取长度

        Returns:
            模块内容字符串
        """
        # 找到模块起始位置
        patterns = [
            rf'"{module_id}":function\(',
            rf'{module_id}:function\(',
        ]

        start_pos = -1
        for pattern in patterns:
            match = re.search(pattern, self.content)
            if match:
                start_pos = match.start()
                break

        if start_pos == -1:
            print(f"[WARN] 未找到模块 {module_id}")
            return None

        # 向后搜索，找到下一个模块的边界
        search_start = start_pos + 50
        search_end = min(start_pos + max_length, len(self.content))

        # 搜索模块结束模式
        end_patterns = [
            r',\s*"[0-9a-fA-F]{4}":function',  # 下一个带引号模块
            r',\s*[0-9a-fA-F]{4}:function',     # 下一个无引号模块
            r'\}\s*\)\s*$',  # 文件结尾
        ]

        earliest_end = search_end
        for pattern in end_patterns:
            match = re.search(pattern, self.content[search_start:search_end])
            if match:
                actual_end = search_start + match.start()
                if actual_end < earliest_end:
                    earliest_end = actual_end

        module_content = self.content[start_pos:earliest_end]

        print(f"[INFO] 提取模块 {module_id} (长度: {len(module_content)})")
        return module_content

    def analyze_dependencies(self, module_content: str) -> Dict[str, str]:
        """
        分析模块中的依赖导入

        Returns:
            {变量名: 模块ID}
        """
        deps = {}

        for pattern in self.DEPENDENCY_PATTERNS:
            matches = re.findall(pattern, module_content)
            for var_name, mod_id in matches:
                deps[var_name] = mod_id
                print(f"  [DEP] {var_name} = n(\"{mod_id}\")")

        return deps

    def search_key_exports(self, module_content: str) -> List[str]:
        """搜索模块中是否有密钥导出"""
        found_keys = []

        for pattern in self.KEY_EXPORT_PATTERNS:
            matches = re.findall(pattern, module_content)
            for export_name in matches:
                if export_name not in found_keys:
                    found_keys.append(export_name)

        if found_keys:
            print(f"  [KEY] 检测到密钥导出: {found_keys}")

        return found_keys

    def search_key_values(self, module_content: str) -> List[str]:
        """搜索模块中的密钥值"""
        values = set()

        for pattern in self.KEY_VALUE_PATTERNS:
            matches = re.findall(pattern, module_content)
            for val in matches:
                # 过滤常见的非密钥值
                if len(val) >= 16 and not val.startswith('0000'):
                    values.add(val)

        sorted_values = sorted(values, key=len)
        for v in sorted_values:
            print(f"  [VALUE] {v} (长度: {len(v)})")

        return sorted_values

    def find_signature_function(self) -> List[dict]:
        """
        查找签名生成函数

        搜索 portal-sign 头附近的函数
        """
        print(f"\n{'='*80}")
        print("[SEARCH] 搜索签名生成函数位置")
        print('='*80)

        # 搜索常见的注入点
        search_patterns = [
            'portal-sign', 'setRequestHeader.*sign',
            'MD5', 'CryptoJS', 'encrypt', 'sign =', '.sign(',
            'n\.d\(e,\s*"e"', 'n\.d\(e,\s*"i"', 'n\.d\(e,\s*"a"',
        ]

        results = []
        for pattern in search_patterns:
            for match in re.finditer(pattern, self.content):
                pos = match.start()
                context = self.content[max(0, pos - 100):pos + 100]
                results.append({
                    'pattern': pattern,
                    'position': pos,
                    'context': context
                })
                print(f"\n匹配 '{pattern}' at {pos}:")
                print(f"  ...{context.strip()}...")

        if not results:
            print("[WARN] 未找到明确的签名函数标记，尝试搜索 MD5 或 AES 相关代码")

        return results

    def extract_and_analyze_module(self, module_id: str, follow_deps: bool = True) -> dict:
        """
        提取并分析单个模块，可选递归分析依赖

        Args:
            module_id: 模块ID
            follow_deps: 是否递归分析依赖

        Returns:
            分析结果字典
        """
        print(f"\n{'='*80}")
        print(f"[ANALYSIS] 分析模块 {module_id}")
        print('='*80)

        content = self.extract_module_content(module_id)
        if not content:
            return {'module_id': module_id, 'found': False}

        # 分析依赖
        print("\n[DEPENDENCIES]")
        deps = self.analyze_dependencies(content)

        # 搜索密钥导出
        print("\n[KEY EXPORTS]")
        key_exports = self.search_key_exports(content)

        # 搜索密钥值
        print("\n[KEY VALUES]")
        key_values = self.search_key_values(content)

        result = {
            'module_id': module_id,
            'found': True,
            'dependencies': deps,
            'has_key_exports': len(key_exports) > 0,
            'key_exports': key_exports,
            'key_values': key_values,
            'content_preview': content[:500] if len(content) > 500 else content
        }

        # 如果有密钥导出，标记为关键模块
        if len(key_exports) >= 2:  # e, i, a 中的至少两个
            print(f"\n[!!] 发现高可疑的密钥模块 {module_id}！")
            result['is_key_module'] = True
            self.key_modules.append(result)

        # 递归分析依赖（寻找真正的密钥模块）
        if follow_deps and deps:
            print(f"\n[RECURSIVE] 正在递归分析 {len(deps)} 个依赖...")
            for var_name, dep_id in deps.items():
                print(f"\n  -> 分析依赖: {var_name} = n(\"{dep_id}\")")
                dep_result = self.extract_and_analyze_module(dep_id, follow_deps=False)

                # 检查这个依赖模块中是否有密钥
                if dep_result.get('has_key_exports'):
                    print(f"\n  [SUCCESS] {var_name} (n(\"{dep_id}\")) 中发现密钥导出！")
                    print(f"               这很可能就是实际的密钥模块！")

        return result

    def find_all_key_modules(self) -> List[dict]:
        """
        自动搜索整个文件中所有可能包含密钥的模块

        Returns:
            所有候选密钥模块列表
        """
        print(f"\n{'='*80}")
        print("[SEARCH] 自动搜索所有可能的密钥模块")
        print('='*80)

        # 搜索所有 n.d(e, "e", ...) 模式，这是密钥导出的特征
        candidates = set()

        for pattern in self.KEY_EXPORT_PATTERNS:
            regex = re.compile(pattern)
            pos = 0
            while True:
                match = regex.search(self.content, pos)
                if not match:
                    break

                pos = match.start()
                # 向前搜索最近的模块ID
                start_search = max(0, pos - 500)
                module_start = re.search(r'"([0-9a-fA-F]{3,10})":function', self.content[start_search:pos])
                module_start2 = re.search(r'([0-9a-fA-F]{3,10}):function', self.content[start_search:pos])

                if module_start:
                    candidates.add(module_start.group(1))
                elif module_start2:
                    candidates.add(module_start2.group(1))

                pos = match.end()

        print(f"[INFO] 找到 {len(candidates)} 个候选密钥模块: {sorted(candidates)}")

        # 分析每个候选模块
        results = []
        for module_id in sorted(candidates):
            result = self.extract_and_analyze_module(module_id, follow_deps=False)
            results.append(result)

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Webpack模块提取工具 - 从打包的JS中提取密钥模块",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  1. 搜索签名函数位置:
     python webpack-module-extractor.py app.js --find-sign-func

  2. 提取并分析指定模块 (关键步骤！):
     python webpack-module-extractor.py app.js --extract-module b775

  3. 自动搜索所有密钥模块:
     python webpack-module-extractor.py app.js --find-keys

  4. 提取密钥模块详细内容:
     python webpack-module-extractor.py app.js --extract-module a078

完整工作流:
  [Step 1] --find-sign-func    → 找 portal-sign 位置
  [Step 2] --extract-module    → 分析签名所在模块，找 r = n("xxx")
  [Step 3] --extract-module    → 分析 xxx 模块提取密钥
        """
    )

    parser.add_argument('js_file', help='JS文件路径')
    parser.add_argument('--find-sign-func', action='store_true', help='搜索签名函数位置')
    parser.add_argument('--find-keys', action='store_true', help='自动搜索所有密钥模块')
    parser.add_argument('--extract-module', '-e', help='提取并分析指定模块')
    parser.add_argument('--no-follow', '-n', action='store_true', help='不递归分析依赖')
    parser.add_argument('--list-modules', '-l', action='store_true', help='列出所有模块ID')
    parser.add_argument('--output', '-o', help='保存分析结果到JSON文件')

    args = parser.parse_args()

    extractor = WebpackModuleExtractor(args.js_file)

    all_results = {}

    if args.list_modules:
        modules = extractor.find_all_modules()
        print("\n所有模块ID:")
        for mid in sorted(modules.keys()):
            print(f"  {mid} @ {modules[mid]}")
        all_results['modules'] = modules

    if args.find_sign_func:
        sign_results = extractor.find_signature_function()
        all_results['signature_locations'] = sign_results

    if args.extract_module:
        module_result = extractor.extract_and_analyze_module(
            args.extract_module,
            follow_deps=not args.no_follow
        )
        all_results['target_module'] = module_result

    if args.find_keys:
        key_module_results = extractor.find_all_key_modules()
        all_results['key_modules'] = key_module_results

        # 输出总结
        print(f"\n{'='*80}")
        print("[SUMMARY] 密钥模块提取总结")
        print('='*80)
        if extractor.key_modules:
            print(f"\n成功找到 {len(extractor.key_modules)} 个高置信度密钥模块:")
            for km in extractor.key_modules:
                print(f"\n  模块ID: {km['module_id']}")
                print(f"  导出的密钥名: {km['key_exports']}")
                print(f"  候选密钥值: {km['key_values'][:10]}")
        else:
            print("\n未找到明确的密钥模块，请尝试以下方法:")
            print("  1. 先用 --find-sign-func 找加密函数位置")
            print("  2. 找到加密函数所在模块ID")
            print("  3. 用 --extract-module 分析该模块的依赖")

    # 保存结果到JSON
    if args.output and all_results:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n[DONE] 分析结果已保存到 {args.output}")


if __name__ == '__main__':
    main()
