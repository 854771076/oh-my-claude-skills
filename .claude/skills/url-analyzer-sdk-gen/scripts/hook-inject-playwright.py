#!/usr/bin/env python3
"""
Playwright Hook注入调试脚本
从hooks目录读取Hook脚本并注入到浏览器中进行调试

使用方式:
    python hook-inject-playwright.py --url "https://example.com" --hook "all-in-one-hook.js"
    python hook-inject-playwright.py --url "https://example.com" --hook-dir "./hooks"
    python hook-inject-playwright.py --url "https://example.com" --list-hooks

特点:
    - 支持init_script在页面加载前注入Hook
    - 实时监听console输出
    - 支持多浏览器(Chromium/Chrome/Edge/Firefox)
    - 支持持久化上下文保存登录态
"""

import os
import sys
import json
import time
import argparse
import logging
import asyncio
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[ERROR] 请先安装Playwright: pip install playwright && playwright install")
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
class PlaywrightHookInjector:
    """Playwright Hook注入器"""

    def __init__(self, options: dict = None):
        self.options = options or {}
        self.output_dir = Path(self.options.get('output_dir', './hook-output'))
        self.headless = self.options.get('headless', False)
        self.wait_time = self.options.get('wait_time', 30)
        self.browser_type = self.options.get('browser_type', 'chromium')
        self.user_data_dir = self.options.get('user_data_dir')
        self.hook_manager = HookManager(self.options.get('hooks_dir'))
        self.intercept_data = []
        self.console_logs = []
        self.network_logs = []

    def setup_output_dir(self):
        """创建输出目录"""
        dirs = ['intercept', 'console', 'network', 'screenshots']
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录: {self.output_dir}")

    async def inject_hook_async(self, url: str, hook_script: str) -> dict:
        """
        异步注入Hook脚本并执行调试

        Args:
            url: 目标URL
            hook_script: Hook脚本内容
        Returns:
            拦截数据和调试结果
        """
        self.setup_output_dir()
        self.intercept_data = []
        self.console_logs = []
        self.network_logs = []

        async with async_playwright() as p:
            # 选择浏览器类型
            browser_launcher = getattr(p, self.browser_type)

            # 浏览器启动配置
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--window-size=1920,1080'
                ]
            }

            # 持久化上下文配置（保存登录态）
            if self.user_data_dir:
                logger.info(f"使用持久化上下文: {self.user_data_dir}")
                context = await browser_launcher.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    **launch_options
                )
            else:
                browser = await browser_launcher.launch(**launch_options)
                context = await browser.new_context()

            # 【关键】在页面加载前注入Hook脚本
            # 使用add_init_script确保脚本在所有页面加载前执行
            await context.add_init_script(hook_script)
            logger.info("Hook脚本已设置为init_script，将在页面加载前注入")

            # 创建页面
            page = await context.new_page()

            # 监听console输出
            page.on('console', lambda msg: self._on_console(msg))

            # 监听网络请求
            page.on('request', lambda req: self._on_request(req))
            page.on('response', lambda res: self._on_response(res))

            try:
                # 访问目标URL
                logger.info(f"正在访问: {url}")
                await page.goto(url, wait_until='networkidle', timeout=60000)

                # 等待页面加载
                await asyncio.sleep(3)

                # 滚动页面触发更多请求
                await self._scroll_page(page)

                # 继续等待收集数据
                logger.info(f"等待收集数据 ({self.wait_time}秒)...")
                await asyncio.sleep(self.wait_time)

                # 获取Hook拦截数据
                try:
                    hook_data = await page.evaluate('window.__hook_export__() || [];')
                    if hook_data:
                        self.intercept_data = hook_data
                        logger.info(f"获取到 {len(hook_data)} 条拦截数据")
                except Exception as e:
                    logger.warning(f"获取Hook数据失败: {e}")

                # 获取页面截图
                screenshot_path = self.output_dir / 'screenshots' / 'page.png'
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"截图保存: {screenshot_path}")

                # 获取页面HTML
                html_content = await page.content()
                html_path = self.output_dir / 'page.html'
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"HTML保存: {html_path}")

                # 获取Cookies
                cookies = await context.cookies()
                cookies_path = self.output_dir / 'cookies.json'
                with open(cookies_path, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2, ensure_ascii=False)
                logger.info(f"Cookies保存: {cookies_path} ({len(cookies)} 个)")

            except Exception as e:
                logger.error(f"Hook注入执行失败: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await context.close()
                logger.info("浏览器上下文已关闭")

        # 保存数据
        self._save_data()

        analysis = self._analyze_intercept_data()
        return {
            'intercept_data': self.intercept_data,
            'console_logs': self.console_logs,
            'network_logs': self.network_logs,
            'keyword_matches': analysis.get('keyword_matches', []),
            'url': url
        }

    def _on_console(self, msg):
        """处理console消息"""
        log_entry = {
            'type': msg.type,
            'text': msg.text,
            'location': msg.location,
            'timestamp': datetime.now().isoformat()
        }
        self.console_logs.append(log_entry)

        # 打印关键日志
        if '[Hook]' in msg.text or 'debugger' in msg.text.lower():
            logger.info(f"[Console] {msg.type}: {msg.text}")

    def _on_request(self, request):
        """处理请求"""
        req_data = {
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
            'post_data': request.post_data,
            'resource_type': request.resource_type,
            'timestamp': datetime.now().isoformat()
        }
        self.network_logs.append({'type': 'request', 'data': req_data})

    def _on_response(self, response):
        """处理响应"""
        res_data = {
            'url': response.url,
            'status': response.status,
            'headers': dict(response.headers),
            'timestamp': datetime.now().isoformat()
        }
        self.network_logs.append({'type': 'response', 'data': res_data})

    async def _scroll_page(self, page):
        """滚动页面触发更多请求"""
        try:
            logger.info("滚动页面以触发更多请求...")
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1)
            logger.info("页面滚动完成")
        except Exception as e:
            logger.warning(f"页面滚动失败: {e}")

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

        # 保存网络日志
        network_path = self.output_dir / 'network' / 'network-logs.json'
        with open(network_path, 'w', encoding='utf-8') as f:
            json.dump(self.network_logs, f, indent=2, ensure_ascii=False)
        logger.info(f"网络日志保存: {network_path}")

        # 分类分析拦截数据
        analysis = self._analyze_intercept_data()
        analysis_path = self.output_dir / 'intercept' / 'analysis.json'
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logger.info(f"分析结果保存: {analysis_path}")

    def _analyze_intercept_data(self) -> dict:
        """分析拦截数据"""
        keywords = self.options.get('keywords', [])

        analysis = {
            'summary': {
                'total_count': len(self.intercept_data),
                'console_count': len(self.console_logs),
                'network_count': len(self.network_logs),
                'types_count': {},
                'keywords': keywords,
                'keyword_matches': 0
            },
            'xhr_requests': [],
            'fetch_requests': [],
            'crypto_operations': [],
            'cookie_operations': [],
            'json_operations': [],
            'keyword_matches': [],
            'hook_console': [],
            'other': []
        }

        def item_contains_keyword(item, keyword: str) -> bool:
            """检查item中是否包含关键词"""
            kw_lower = keyword.lower()
            # 检查type
            if kw_lower in item.get('type', '').lower():
                return True
            # 检查data字段
            data_str = json.dumps(item.get('data', {}), ensure_ascii=False).lower()
            if kw_lower in data_str:
                return True
            return False

        # 分析Hook拦截数据
        for item in self.intercept_data:
            type_name = item.get('type', 'unknown')
            analysis['summary']['types_count'][type_name] = analysis['summary']['types_count'].get(type_name, 0) + 1

            # 关键词匹配
            matched_keywords = [k for k in keywords if item_contains_keyword(item, k)]
            if matched_keywords:
                item_copy = dict(item)
                item_copy['_matched_keywords'] = matched_keywords
                analysis['keyword_matches'].append(item_copy)
                analysis['summary']['keyword_matches'] += 1

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

        # 分析console日志（提取Hook相关）
        for log in self.console_logs:
            if '[Hook]' in log.get('text', '') or 'debugger' in log.get('text', '').lower():
                analysis['hook_console'].append(log)

        # 分析网络请求
        xhr_count = sum(1 for log in self.network_logs
                       if log.get('type') == 'request'
                       and log.get('data', {}).get('resource_type') in ['xhr', 'fetch'])
        analysis['summary']['xhr_fetch_count'] = xhr_count

        # 分析加密特征
        if analysis['crypto_operations']:
            analysis['crypto_summary'] = {
                'algorithms_used': list(set(item.get('type') for item in analysis['crypto_operations'])),
                'sample_inputs': [item.get('data', {}).get('input', '')[:50] for item in analysis['crypto_operations'][:3]]
            }

        return analysis

    def inject_hook(self, url: str, hook_script: str) -> dict:
        """同步接口"""
        return asyncio.run(self.inject_hook_async(url, hook_script))


def main():
    parser = argparse.ArgumentParser(
        description='Playwright Hook注入调试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 列出所有可用的Hook脚本
  python hook-inject-playwright.py --list-hooks

  # 使用综合Hook调试（Chromium）
  python hook-inject-playwright.py --url "https://example.com" --hook "all-in-one-hook.js"

  # 使用Chrome浏览器
  python hook-inject-playwright.py --url "https://example.com" --browser chrome

  # 使用持久化上下文保存登录态
  python hook-inject-playwright.py --url "https://example.com" --user-data-dir "./browser-data"

  # 调试加密参数
  python hook-inject-playwright.py --url "https://api.example.com/sign" --hook "crypto-hook.js" --wait 60

特点:
  - init_script注入：Hook脚本在页面加载前执行，确保不漏过任何请求
  - 实时console监听：所有console.log输出都会被捕获
  - 网络请求监听：记录所有XHR/Fetch请求和响应
  - 多浏览器支持：chromium/chrome/edge/firefox
  - 持久化上下文：保存登录态，下次运行自动恢复
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
    parser.add_argument('--browser', choices=['chromium', 'chrome', 'edge', 'firefox'],
                        default='chromium', help='浏览器类型')
    parser.add_argument('--user-data-dir', help='持久化上下文目录（保存登录态）')

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
        'browser_type': args.browser,
        'user_data_dir': args.user_data_dir,
        'hooks_dir': args.hook_dir,
        'keywords': [k.strip() for k in args.keywords.split(',')] if args.keywords else []
    }

    # 执行Hook注入
    injector = PlaywrightHookInjector(options)
    result = injector.inject_hook(args.url, hook_script)

    # 输出结果摘要
    print("\n" + "="*60)
    print("[Hook注入调试结果]")
    print("="*60)
    print(f"  URL: {args.url}")
    print(f"  Hook: {args.hook}")
    print(f"  浏览器: {args.browser}")
    print(f"  拦截数据: {len(result['intercept_data'])} 条")
    print(f"  Console日志: {len(result['console_logs'])} 条")
    print(f"  网络日志: {len(result['network_logs'])} 条")

    # 分类统计
    if result['intercept_data']:
        types_count = {}
        for item in result['intercept_data']:
            t = item.get('type', 'unknown')
            types_count[t] = types_count.get(t, 0) + 1
        print("\n  拦截类型统计:")
        for t, count in sorted(types_count.items()):
            print(f"    - {t}: {count} 条")

    # Hook相关console日志
    hook_logs = [log for log in result['console_logs'] if '[Hook]' in log.get('text', '')]
    if hook_logs:
        print("\n  Hook Console日志（最近10条）:")
        for log in hook_logs[-10:]:
            print(f"    [{log['type']}] {log['text'][:100]}")

    # 关键词匹配结果
    if args.keywords and result.get('keyword_matches'):
        print(f"\n  关键词匹配结果 ({len(result['keyword_matches'])} 条):")
        for match in result['keyword_matches'][:10]:  # 最多显示10条
            matched = ', '.join(match.get('_matched_keywords', []))
            print(f"    - [{matched}] {match.get('type', 'unknown')}")
        if len(result['keyword_matches']) > 10:
            print(f"      ... 还有 {len(result['keyword_matches']) - 10} 条匹配结果")

    print("="*60)
    print(f"\n[OUTPUT] 拦截数据: {args.output}/intercept/hook-data.json")
    print(f"[OUTPUT] 分析结果: {args.output}/intercept/analysis.json")
    print(f"[OUTPUT] Console日志: {args.output}/console/console-logs.json")
    print(f"[OUTPUT] 网络日志: {args.output}/network/network-logs.json")
    print(f"[OUTPUT] 页面截图: {args.output}/screenshots/page.png")
    print(f"[OUTPUT] 页面HTML: {args.output}/page.html")
    print(f"[OUTPUT] Cookies: {args.output}/cookies.json")


if __name__ == '__main__':
    main()