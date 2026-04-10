#!/usr/bin/env python3
"""
DrissionPage Hook注入调试脚本
从hooks目录读取Hook脚本并注入到浏览器中进行调试

使用方式:
    python hook-inject-drissionpage.py --url "https://example.com" --hook "all-in-one-hook.js"
    python hook-inject-drissionpage.py --url "https://example.com" --hook-dir "./hooks"
    python hook-inject-drissionpage.py --url "https://example.com" --list-hooks
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    print("[ERROR] 请先安装DrissionPage: pip install DrissionPage")
    sys.exit(1)


# ============== 日志配置 ==============
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger('HookInject')


# ============== Hook管理 ==============
class HookManager:
    """Hook脚本管理器"""

    DEFAULT_HOOKS_DIR = Path(__file__).parent.parent / 'hooks'

    AVAILABLE_HOOKS = {
        'all-in-one-hook.js': {
            'name': '综合Hook',
            'description': '包含所有常用Hook：Cookie、XHR、Fetch、JSON、加密库等',
            'features': ['cookie', 'xhr', 'fetch', 'json', 'crypto', 'debugger', 'websocket']
        },
        'xhr-hook.js': {
            'name': 'XHR Hook',
            'description': '拦截XHR请求，记录请求参数和响应',
            'features': ['xhr']
        },
        'fetch-hook.js': {
            'name': 'Fetch Hook',
            'description': '拦截Fetch请求，记录请求参数和响应',
            'features': ['fetch']
        },
        'crypto-hook.js': {
            'name': '加密Hook',
            'description': '拦截CryptoJS、Base64等加密函数调用',
            'features': ['crypto', 'md5', 'sha', 'aes', 'base64']
        },
        'debug-hook.js': {
            'name': '调试Hook',
            'description': '在关键函数处设置断点，搜索sign相关函数',
            'features': ['debug', 'sign-search']
        }
    }

    def __init__(self, hooks_dir: str = None):
        self.hooks_dir = Path(hooks_dir) if hooks_dir else self.DEFAULT_HOOKS_DIR
        if not self.hooks_dir.exists():
            logger.warning(f"Hooks目录不存在: {self.hooks_dir}")
            self.hooks_dir = self.DEFAULT_HOOKS_DIR

    def list_hooks(self) -> dict:
        """列出所有可用的Hook脚本"""
        hooks = {}
        for hook_file in self.hooks_dir.glob('*.js'):
            hook_name = hook_file.name
            info = self.AVAILABLE_HOOKS.get(hook_name, {
                'name': hook_name,
                'description': '自定义Hook脚本',
                'features': []
            })
            info['path'] = str(hook_file)
            info['size'] = hook_file.stat().st_size
            hooks[hook_name] = info
        return hooks

    def load_hook(self, hook_name: str) -> str:
        """加载指定的Hook脚本内容"""
        hook_path = self.hooks_dir / hook_name
        if not hook_path.exists():
            # 尝试在默认目录查找
            hook_path = self.DEFAULT_HOOKS_DIR / hook_name
            if not hook_path.exists():
                raise FileNotFoundError(f"Hook脚本不存在: {hook_name}")

        with open(hook_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"加载Hook脚本: {hook_path} ({len(content)} bytes)")
        return content

    def load_all_hooks(self) -> str:
        """加载并合并所有Hook脚本"""
        combined = []
        for hook_file in self.hooks_dir.glob('*.js'):
            if hook_file.name != 'all-in-one-hook.js':  # 跳过综合脚本避免重复
                content = self.load_hook(hook_file.name)
                combined.append(f"\n// === {hook_file.name} ===\n{content}")

        return "\n".join(combined)


# ============== Hook注入器 ==============
class DrissionPageHookInjector:
    """DrissionPage Hook注入器"""

    def __init__(self, options: dict = None):
        self.options = options or {}
        self.output_dir = Path(self.options.get('output_dir', './hook-output'))
        self.headless = self.options.get('headless', False)
        self.wait_time = self.options.get('wait_time', 30)
        self.hook_manager = HookManager(self.options.get('hooks_dir'))
        self.intercept_data = []
        self.console_logs = []

    def setup_output_dir(self):
        """创建输出目录"""
        dirs = ['intercept', 'console', 'screenshots']
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录: {self.output_dir}")

    def inject_hook(self, url: str, hook_script: str) -> dict:
        """
        注入Hook脚本并执行调试

        Args:
            url: 目标URL
            hook_script: Hook脚本内容
        Returns:
            拦截数据和调试结果
        """
        self.setup_output_dir()
        self.intercept_data = []
        self.console_logs = []

        # 创建浏览器配置
        co = ChromiumOptions()
        if self.headless:
            co.headless(True)

        # 防止被检测为自动化
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--window-size=1920,1080')

        # 设置开发者工具自动打开（调试模式）
        if not self.headless:
            co.set_argument('--auto-open-devtools-for-tabs')

        logger.info(f"正在访问: {url}")

        # 创建页面对象
        page = ChromiumPage(co)

        try:
            # 【关键】DrissionPage注入JS脚本的方式
            # 方法1: 使用page.run_js()在页面加载前注入
            # 方法2: 监听console输出

            # 先访问页面
            page.get(url)
            time.sleep(2)

            # 注入Hook脚本
            logger.info("注入Hook脚本...")
            page.run_js(hook_script)
            logger.info("Hook脚本注入成功")

            # 等待页面加载和Hook执行
            time.sleep(5)

            # 滚动页面触发更多请求
            try:
                page.scroll.to_bottom()
                time.sleep(2)
                page.scroll.to_top()
                time.sleep(1)
            except Exception as e:
                logger.warning(f"滚动页面失败: {e}")

            # 继续等待收集数据
            logger.info(f"等待收集数据 ({self.wait_time}秒)...")
            time.sleep(self.wait_time)

            # 获取Hook拦截数据
            try:
                hook_data = page.run_js('return window.__hook_export__() || [];')
                if hook_data:
                    self.intercept_data = hook_data
                    logger.info(f"获取到 {len(hook_data)} 条拦截数据")
            except Exception as e:
                logger.warning(f"获取Hook数据失败: {e}")

            # 获取页面截图
            try:
                screenshot_path = self.output_dir / 'screenshots' / 'page.png'
                page.get_screenshot(path=str(screenshot_path))
                logger.info(f"截图保存: {screenshot_path}")
            except Exception as e:
                logger.warning(f"截图失败: {e}")

            # 获取console日志（通过监听）
            # DrissionPage 4.x 使用 listen 监听 console
            try:
                page.listen.set_targets(targets='console')
                page.listen.start()
                for packet in page.listen.steps(timeout=5):
                    if hasattr(packet, 'text'):
                        self.console_logs.append({
                            'type': getattr(packet, 'type', 'log'),
                            'text': packet.text,
                            'timestamp': datetime.now().isoformat()
                        })
                page.listen.stop()
            except Exception as e:
                logger.warning(f"监听console失败: {e}")

        except Exception as e:
            logger.error(f"Hook注入执行失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                page.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器出错: {e}")

        # 保存数据
        self._save_data()

        return {
            'intercept_data': self.intercept_data,
            'console_logs': self.console_logs,
            'url': url
        }

    def _save_data(self):
        """保存拦截数据"""
        # 保存拦截数据
        intercept_path = self.output_dir / 'intercept' / 'hook-data.json'
        with open(intercept_path, 'w', encoding='utf-8') as f:
            json.dump(self.intercept_data, f, indent=2, ensure_ascii=False)
        logger.info(f"拦截数据保存: {intercept_path}")

        # 保存console日志
        console_path = self.output_dir / 'console' / 'console-logs.json'
        with open(console_path, 'w', encoding='utf-8') as f:
            json.dump(self.console_logs, f, indent=2, ensure_ascii=False)
        logger.info(f"Console日志保存: {console_path}")

        # 分类分析拦截数据
        analysis = self._analyze_intercept_data()
        analysis_path = self.output_dir / 'intercept' / 'analysis.json'
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logger.info(f"分析结果保存: {analysis_path}")

    def _analyze_intercept_data(self) -> dict:
        """分析拦截数据"""
        analysis = {
            'summary': {
                'total_count': len(self.intercept_data),
                'types_count': {}
            },
            'xhr_requests': [],
            'fetch_requests': [],
            'crypto_operations': [],
            'cookie_operations': [],
            'json_operations': [],
            'other': []
        }

        for item in self.intercept_data:
            type_name = item.get('type', 'unknown')
            analysis['summary']['types_count'][type_name] = analysis['summary']['types_count'].get(type_name, 0) + 1

            # 分类存储
            if type_name.startswith('xhr'):
                analysis['xhr_requests'].append(item)
            elif type_name.startswith('fetch'):
                analysis['fetch_requests'].append(item)
            elif type_name in ['md5', 'sha256', 'aes', 'btoa', 'atob', 'crypto']:
                analysis['crypto_operations'].append(item)
            elif type_name.startswith('cookie'):
                analysis['cookie_operations'].append(item)
            elif type_name in ['stringify', 'parse']:
                analysis['json_operations'].append(item)
            else:
                analysis['other'].append(item)

        # 分析加密特征
        if analysis['crypto_operations']:
            analysis['crypto_summary'] = {
                'algorithms_used': list(set(item.get('type') for item in analysis['crypto_operations'])),
                'sample_inputs': [item.get('data', {}).get('input', '')[:50] for item in analysis['crypto_operations'][:3]]
            }

        return analysis


def main():
    parser = argparse.ArgumentParser(
        description='DrissionPage Hook注入调试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 列出所有可用的Hook脚本
  python hook-inject-drissionpage.py --list-hooks

  # 使用综合Hook调试
  python hook-inject-drissionpage.py --url "https://example.com" --hook "all-in-one-hook.js"

  # 使用特定Hook调试
  python hook-inject-drissionpage.py --url "https://example.com" --hook "crypto-hook.js"

  # 使用自定义Hooks目录
  python hook-inject-drissionpage.py --url "https://example.com" --hook-dir "./custom-hooks" --hook "my-hook.js"

  # 有头模式（显示浏览器）
  python hook-inject-drissionpage.py --url "https://example.com" --hook "all-in-one-hook.js" --headed

  # 调试加密参数
  python hook-inject-drissionpage.py --url "https://api.example.com/sign" --hook "crypto-hook.js" --wait 60
        '''
    )

    parser.add_argument('--url', '-u', help='目标URL')
    parser.add_argument('--output', '-o', default='./hook-output', help='输出目录')
    parser.add_argument('--wait', '-w', type=int, default=30, help='等待时间(秒)')

    # Hook配置
    parser.add_argument('--hook', '-h', default='all-in-one-hook.js', help='Hook脚本名称')
    parser.add_argument('--hook-dir', help='自定义Hooks目录')
    parser.add_argument('--list-hooks', action='store_true', help='列出所有可用的Hook脚本')

    # 浏览器配置
    parser.add_argument('--headed', action='store_true', help='有头模式（显示浏览器）')

    # 分析配置
    parser.add_argument('--keywords', '-k', help='额外监控的关键词（逗号分隔）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细日志')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Hook管理器
    hook_manager = HookManager(args.hook_dir)

    # 仅列出可用的Hook
    if args.list_hooks:
        hooks = hook_manager.list_hooks()
        print("\n" + "="*60)
        print("可用的Hook脚本:")
        print("="*60)
        for name, info in hooks.items():
            print(f"\n【{info['name']}】 {name}")
            print(f"  描述: {info['description']}")
            print(f"  功能: {', '.join(info['features'])}")
            print(f"  路径: {info['path']}")
            print(f"  大小: {info['size']} bytes")
        print("\n" + "="*60)
        return

    # URL是必需的
    if not args.url:
        parser.error("需要提供 --url 参数（或使用 --list-hooks 查看可用Hook）")

    # 加载Hook脚本
    try:
        hook_script = hook_manager.load_hook(args.hook)
        print(f"\n[Hook] 加载脚本: {args.hook}")
        print(f"[Hook] 脚本大小: {len(hook_script)} bytes")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return

    # 构建配置
    options = {
        'url': args.url,
        'output_dir': args.output,
        'headless': not args.headed,
        'wait_time': args.wait,
        'hooks_dir': args.hook_dir
    }

    # 执行Hook注入
    injector = DrissionPageHookInjector(options)
    result = injector.inject_hook(args.url, hook_script)

    # 输出结果摘要
    print("\n" + "="*60)
    print("[Hook注入调试结果]")
    print("="*60)
    print(f"  URL: {args.url}")
    print(f"  Hook: {args.hook}")
    print(f"  拦截数据: {len(result['intercept_data'])} 条")
    print(f"  Console日志: {len(result['console_logs'])} 条")

    # 分类统计
    if result['intercept_data']:
        types_count = {}
        for item in result['intercept_data']:
            t = item.get('type', 'unknown')
            types_count[t] = types_count.get(t, 0) + 1
        print("\n  拦截类型统计:")
        for t, count in sorted(types_count.items()):
            print(f"    - {t}: {count} 条")

    print("="*60)
    print(f"\n[OUTPUT] 拦截数据: {args.output}/intercept/hook-data.json")
    print(f"[OUTPUT] 分析结果: {args.output}/intercept/analysis.json")
    print(f"[OUTPUT] Console日志: {args.output}/console/console-logs.json")
    print(f"[OUTPUT] 页面截图: {args.output}/screenshots/page.png")


if __name__ == '__main__':
    main()