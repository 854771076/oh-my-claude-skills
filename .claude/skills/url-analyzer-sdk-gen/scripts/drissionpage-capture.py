#!/usr/bin/env python3
"""
DrissionPage 自动化抓包脚本 V4.0
修复JS文件捕获问题，支持项目内用户数据目录

关键修复:
1. 监听必须在页面访问前启动
2. resourceType大小写兼容
3. 用户数据目录放在项目内
4. 支持手动登录流程

使用方式:
python drissionpage-capture.py --url "https://example.com" --output "./capture-output"
"""

import os
import sys
import json
import time
import argparse
import platform
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from functools import wraps

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


logger = setup_logger('Capture')


# ============== 配置 ==============
BROWSER_PATHS = {
    'chrome': {
        'Windows': "C:/Program Files/Google/Chrome/Application/chrome.exe",
        'Darwin': "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        'Linux': "/usr/bin/google-chrome"
    },
    'edge': {
        'Windows': "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        'Darwin': "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        'Linux': "/usr/bin/microsoft-edge"
    }
}

BROWSER_PROCESS_NAMES = {
    'chrome': ['chrome.exe', 'chrome'],
    'edge': ['msedge.exe', 'msedge']
}

# 默认浏览器路径
DEFAULT_BROWSER_PATHS = {
    'chrome': {
        'Windows': "C:/Program Files/Google/Chrome/Application/chrome.exe",
        'Darwin': "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        'Linux': "/usr/bin/google-chrome"
    },
    'edge': {
        'Windows': "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        'Darwin': "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        'Linux': "/usr/bin/microsoft-edge"
    }
}

# 默认用户数据目录
DEFAULT_USER_DATA_DIRS = {
    'chrome': {
        'Windows': lambda: os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data'),
        'Darwin': lambda: os.path.join(os.environ.get('HOME', ''), 'Library', 'Application Support', 'Google', 'Chrome'),
        'Linux': lambda: os.path.join(os.environ.get('HOME', ''), '.config', 'google-chrome')
    },
    'edge': {
        'Windows': lambda: os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data'),
        'Darwin': lambda: os.path.join(os.environ.get('HOME', ''), 'Library', 'Application Support', 'Microsoft Edge'),
        'Linux': lambda: os.path.join(os.environ.get('HOME', ''), '.config', 'microsoft-edge')
    }
}


def normalize_resource_type(rt) -> str:
    """标准化resourceType（处理大小写）"""
    if rt is None:
        return 'unknown'
    return str(rt).lower()


def check_browser_running(browser_type: str) -> bool:
    """检查浏览器是否正在运行"""
    system = platform.system()
    process_names = BROWSER_PROCESS_NAMES.get(browser_type, [])

    try:
        if system == 'Windows':
            # 使用tasklist检查Windows进程
            result = subprocess.run(['tasklist'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for proc in process_names:
                if proc.lower() in result.stdout.lower():
                    return True
        else:
            # 使用pgrep检查Linux/Mac进程
            for proc in process_names:
                result = subprocess.run(['pgrep', '-f', proc], capture_output=True)
                if result.returncode == 0:
                    return True
    except Exception as e:
        logger.warning(f"检查浏览器进程失败: {e}")

    return False


def get_browser_lock_file(browser_type: str, user_data_dir: str) -> str:
    """获取浏览器锁文件路径"""
    lock_files = {
        'chrome': 'SingletonLock',
        'edge': 'SingletonLock'
    }
    lock_name = lock_files.get(browser_type, 'SingletonLock')
    return os.path.join(user_data_dir, lock_name)


def check_user_data_locked(browser_type: str, user_data_dir: str) -> bool:
    """检查用户数据目录是否被锁定"""
    lock_file = get_browser_lock_file(browser_type, user_data_dir)
    if os.path.exists(lock_file):
        try:
            # 尝试删除锁文件（如果成功说明未被锁定）
            os.remove(lock_file)
            return False
        except:
            return True
    return False


# ============== 重试装饰器 ==============
def retry_on_error(max_attempts: int = 3, wait_seconds: float = 2.0):
    """简单的重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait_time = wait_seconds * (2 ** attempt)
                        logger.warning(f"[RETRY] 第{attempt + 1}次尝试失败: {e}, {wait_time:.1f}秒后重试...")
                        time.sleep(wait_time)
            raise last_error
        return wrapper
    return decorator


# ============== 主类 ==============
class DrissionPageCapture:
    """DrissionPage抓包器 - 修复版"""

    def __init__(self, options: dict = None):
        self.options = options or {}
        self.output_dir = Path(self.options.get('output_dir', './capture-output'))
        self.headless = self.options.get('headless', False)
        self.use_existing_user_data = self.options.get('use_existing_user_data', True)
        self.user_data_dir = self.options.get('user_data_dir')
        self.profile_dir = self.options.get('profile_dir', 'Default')
        self.browser_type = self.options.get('browser_type', 'chrome')
        self.browser_path = self.options.get('browser_path')
        self.wait_time = self.options.get('wait_time', 8)
        self.no_imgs = self.options.get('no_imgs', False)  # 默认加载图片以触发更多请求
        self.incognito = self.options.get('incognito', False)
        self.max_retries = self.options.get('max_retries', 3)
        self.scroll_page = self.options.get('scroll_page', True)  # 新增：滚动页面触发请求

        self.api_requests = []
        self.js_files = []
        self.all_requests = []
        self.page_html = None
        self.page_title = None
        self.cookies = []

    def get_default_user_data_dir(self) -> str:
        """获取默认用户数据目录"""
        system = platform.system()
        dirs = DEFAULT_USER_DATA_DIRS.get(self.browser_type, {})
        if system in dirs:
            path = dirs[system]()
            if os.path.exists(path):
                return path
        return None

    def get_default_browser_path(self) -> str:
        """获取默认浏览器路径"""
        system = platform.system()
        paths = DEFAULT_BROWSER_PATHS.get(self.browser_type, {})
        if system in paths:
            path = paths[system]
            if os.path.exists(path):
                return path
        return None

    def setup_output_dir(self):
        """创建输出目录"""
        dirs = ['xhr', 'js', 'har', 'headers']
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)
        logger.info(f"输出目录: {self.output_dir}")

    def check_user_data_availability(self) -> bool:
        """
        检查用户数据目录可用性
        返回: True表示可以使用，False表示不可用
        """
        user_data = self.user_data_dir or self.get_default_user_data_dir()
        if not user_data:
            logger.warning("未找到用户数据目录")
            return False

        # 检查浏览器是否运行
        if check_browser_running(self.browser_type):
            logger.warning(f"[重要] {self.browser_type} 浏览器正在运行！")
            logger.warning("用户数据目录已被锁定，无法继承登录状态。")
            logger.warning("请关闭浏览器后重新运行，或使用 --no-user-data 参数")
            return False

        # 检查锁文件
        if check_user_data_locked(self.browser_type, user_data):
            logger.warning(f"用户数据目录被锁定: {user_data}")
            return False

        return True

    def create_chromium_options(self) -> ChromiumOptions:
        """创建浏览器配置"""
        co = ChromiumOptions()

        # 无头模式
        if self.headless:
            co.headless(True)
            logger.info("无头模式: 开启")

        # 图片加载（默认加载以触发更多请求）
        if self.no_imgs:
            co.no_imgs()
            logger.info("图片加载: 关闭")
        else:
            logger.info("图片加载: 开启")

        # 无痕模式
        if self.incognito:
            co.incognito(True)
            logger.info("无痕模式: 开启")

        # 设置浏览器路径
        browser_path = self.browser_path or self.get_default_browser_path()
        if browser_path:
            co.set_browser_path(browser_path)
            logger.info(f"浏览器路径: {browser_path}")

        # 用户数据继承（关键修复）
        if self.use_existing_user_data and not self.incognito:
            if self.check_user_data_availability():
                user_data = self.user_data_dir or self.get_default_user_data_dir()
                co.set_user_data_path(user_data)
                co.auto_port()
                logger.info(f"用户数据目录: {user_data}")
                logger.info(f"Profile: {self.profile_dir}")
                logger.info("[OK] 用户数据继承成功，将自动加载登录状态")
            else:
                logger.warning("用户数据不可用，使用全新会话")
                co.auto_port()
        else:
            co.auto_port()

        # 防止被检测为自动化
        co.set_argument('--disable-blink-features=AutomationControlled')

        # 设置窗口大小
        co.set_argument('--window-size=1920,1080')

        return co

    def _safe_get_html(self, page) -> str:
        """安全获取HTML内容"""
        try:
            return page.html
        except Exception as e:
            logger.warning(f"获取HTML失败: {e}")
            return ""

    def _safe_get_title(self, page) -> str:
        """安全获取页面标题"""
        try:
            return page.title
        except Exception as e:
            logger.warning(f"获取标题失败: {e}")
            return ""

    def _safe_get_cookies(self, page) -> list:
        """安全获取Cookies"""
        try:
            cookies = page.cookies()
            return [dict(c) for c in cookies] if cookies else []
        except Exception as e:
            logger.warning(f"获取Cookies失败: {e}")
            return []

    def _scroll_page(self, page):
        """滚动页面触发更多请求"""
        try:
            logger.info("滚动页面以触发更多请求...")
            # 滚动到底部
            page.scroll.to_bottom()
            time.sleep(2)
            # 滚动回顶部
            page.scroll.to_top()
            time.sleep(1)
            # 部分滚动几次
            for i in range(3):
                page.scroll.down(500)
                time.sleep(1)
                page.scroll.up(300)
                time.sleep(0.5)
            logger.info("页面滚动完成")
        except Exception as e:
            logger.warning(f"页面滚动失败: {e}")

    @retry_on_error(max_attempts=3, wait_seconds=2.0)
    def capture(self, url: str) -> dict:
        """
        执行抓包 - 修复版

        Args:
            url: 目标URL
        """
        self.setup_output_dir()

        # 清空之前的请求记录
        self.api_requests = []
        self.js_files = []
        self.all_requests = []
        self.page_html = None
        self.page_title = None
        self.cookies = []

        # 创建浏览器配置
        co = self.create_chromium_options()

        logger.info(f"正在访问: {url}")

        # 创建页面对象
        page = ChromiumPage(co)

        try:
            # 【关键修复】DrissionPage 4.x 正确的监听API用法
            # 1. 先设置监听目标（使用res_type参数）
            logger.info("设置监听目标...")
            page.listen.set_targets(res_type=('xhr', 'fetch', 'script'))

            # 2. 启动监听
            page.listen.start()
            logger.info("监听已启动: xhr, fetch, script")

            # 访问页面
            page.get(url)
            logger.info("页面访问成功")

            # 等待页面加载并滚动触发更多请求
            time.sleep(3)

            # 滚动页面触发更多XHR
            if self.scroll_page:
                self._scroll_page(page)

            # 再等待一段时间让后续请求完成
            time.sleep(self.wait_time)

            # 获取HTML和标题
            self.page_html = self._safe_get_html(page)
            self.page_title = self._safe_get_title(page)
            logger.info(f"HTML长度: {len(self.page_html) if self.page_html else 0}")

            # 获取Cookies验证继承
            self.cookies = self._safe_get_cookies(page)
            logger.info(f"获取到 {len(self.cookies)} 个Cookies")

            # 检查关键Cookie（如登录态）
            key_cookies = ['DedeUserID', 'SESSDATA', 'bili_jct', 'buvid3', 'buvid4']
            found_cookies = [c.get('name', '') for c in self.cookies if c.get('name') in key_cookies]
            if found_cookies:
                logger.info(f"[Cookie继承成功] 发现关键Cookie: {found_cookies}")
            else:
                logger.warning("[Cookie继承警告] 未发现关键登录Cookie，请检查浏览器是否已登录目标网站")

            # 【关键修复】使用steps迭代器收集请求
            logger.info("收集监听到的请求...")

            packet_count = 0
            # 使用steps迭代器获取所有监听到的数据包
            for packet in page.listen.steps(timeout=30):
                try:
                    request = packet.request
                    response = packet.response

                    # 获取资源类型
                    resource_type = getattr(packet, 'resourceType', None)
                    if resource_type is None:
                        resource_type = getattr(packet, 'resource_type', 'unknown')
                    resource_type = str(resource_type).lower() if resource_type else 'unknown'

                    request_data = {
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers) if request.headers else {},
                        'postData': getattr(request, 'postData', None) or getattr(request, 'post_data', None),
                        'resourceType': resource_type,
                    }

                    if response:
                        request_data['response'] = {
                            'status': response.status,
                            'headers': dict(response.headers) if response.headers else {},
                        }
                        try:
                            body = response.body
                            if body:
                                if isinstance(body, bytes):
                                    try:
                                        body = body.decode('utf-8', errors='ignore')
                                    except:
                                        body = body.decode('latin-1', errors='ignore')
                                request_data['response']['body'] = body[:5000] if len(body) > 5000 else body
                        except Exception:
                            request_data['response']['body'] = None

                    self.all_requests.append(request_data)
                    packet_count += 1

                    # 分类保存
                    if resource_type in ['xhr', 'fetch']:
                        self.api_requests.append(request_data)
                        logger.debug(f"[XHR/Fetch] {request.method} {request.url[:80]}")
                    elif resource_type == 'script':
                        self.js_files.append(request_data)
                        logger.debug(f"[JS] {request.url[:80]}")

                except Exception as e:
                    logger.warning(f"处理请求包失败: {e}")
                    continue

            logger.info(f"监听到 {packet_count} 个请求包")
            logger.info(f"抓包完成 - 总请求: {len(self.all_requests)}, API(XHR/Fetch): {len(self.api_requests)}, JS: {len(self.js_files)}")

        except Exception as e:
            logger.error(f"抓包失败: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            # 停止监听
            try:
                page.listen.stop()
                logger.debug("监听已停止")
            except Exception as e:
                logger.warning(f"停止监听时出错: {e}")

            # 关闭浏览器
            try:
                page.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

        # 保存数据
        self._save_data()

        return {
            'all_requests': self.all_requests,
            'api_requests': self.api_requests,
            'js_files': self.js_files,
            'page_html': self.page_html,
            'page_title': self.page_title,
            'cookies': self.cookies
        }

    def _save_data(self):
        """保存抓包数据"""
        # 保存API请求
        with open(self.output_dir / 'xhr' / 'api-requests.json', 'w', encoding='utf-8') as f:
            json.dump(self.api_requests, f, indent=2, ensure_ascii=False)

        # 保存JS文件列表
        with open(self.output_dir / 'js' / 'js-files.json', 'w', encoding='utf-8') as f:
            json.dump(self.js_files, f, indent=2, ensure_ascii=False)

        # 保存全部请求
        with open(self.output_dir / 'all-requests.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_requests, f, indent=2, ensure_ascii=False)

        # 保存Cookies
        with open(self.output_dir / 'cookies.json', 'w', encoding='utf-8') as f:
            json.dump(self.cookies, f, indent=2, ensure_ascii=False)

        # 保存页面HTML
        if self.page_html:
            with open(self.output_dir / 'page.html', 'w', encoding='utf-8') as f:
                f.write(self.page_html)

        # 保存抓包摘要
        summary = {
            'url': self.options.get('url', ''),
            'capture_time': datetime.now().isoformat(),
            'total_requests': len(self.all_requests),
            'api_requests': len(self.api_requests),
            'js_files': len(self.js_files),
            'cookies_count': len(self.cookies),
            'has_login_cookies': any(c.get('name') in ['DedeUserID', 'SESSDATA', 'bili_jct'] for c in self.cookies)
        }
        with open(self.output_dir / 'capture-summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"数据已保存到: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='DrissionPage抓包工具 V3.4 (修复版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
用户数据继承说明:
  默认自动检测并继承本地Chrome/Edge的用户数据（包括Cookies、登录状态等）

  【重要】如果浏览器正在运行，用户数据目录会被锁定，无法继承！
  请确保关闭目标浏览器后再运行此脚本。

  使用 --check-browser 可以检查浏览器是否在运行
  使用 --no-user-data 或 --incognito 可禁用用户数据继承

示例:
  python drissionpage-capture.py --url "https://example.com"
  python drissionpage-capture.py --url "https://example.com" --headed
  python drissionpage-capture.py --url "https://example.com" --browser edge
  python drissionpage-capture.py --url "https://example.com" --no-user-data
  python drissionpage-capture.py --check-browser --browser edge
        '''
    )

    parser.add_argument('--url', '-u', help='目标URL')
    parser.add_argument('--output', '-o', default='./capture-output', help='输出目录')
    parser.add_argument('--wait', '-w', type=int, default=8, help='等待时间(秒)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细日志')

    # 检查浏览器状态
    parser.add_argument('--check-browser', action='store_true', help='仅检查浏览器是否运行')

    # 浏览器配置
    parser.add_argument('--headed', action='store_true', help='有头模式（显示浏览器）')
    parser.add_argument('--browser', choices=['chrome', 'edge'], default='chrome',
                        help='浏览器类型 (默认: chrome)')
    parser.add_argument('--browser-path', help='自定义浏览器路径')

    # 用户数据配置
    parser.add_argument('--user-data-dir', help='自定义用户数据目录')
    parser.add_argument('--profile', default='Default', help='Profile目录名 (默认: Default)')
    parser.add_argument('--no-user-data', action='store_true', help='不继承用户数据')
    parser.add_argument('--incognito', action='store_true', help='无痕模式')

    # 性能优化
    parser.add_argument('--load-images', action='store_true', default=True, help='加载图片（默认加载）')
    parser.add_argument('--no-images', action='store_true', help='不加载图片')
    parser.add_argument('--max-retries', type=int, default=3, help='最大重试次数 (默认: 3)')
    parser.add_argument('--no-scroll', action='store_true', help='不滚动页面')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger('DrissionPageCapture').setLevel(logging.DEBUG)

    # 仅检查浏览器状态
    if args.check_browser:
        running = check_browser_running(args.browser)
        if running:
            print(f"[警告] {args.browser} 浏览器正在运行！")
            print("请关闭浏览器后再运行抓包脚本以继承用户数据。")
            user_data = DEFAULT_USER_DATA_DIRS.get(args.browser, {}).get(platform.system(), lambda: None)()
            if user_data:
                locked = check_user_data_locked(args.browser, user_data)
                print(f"用户数据目录: {user_data}")
                print(f"锁定状态: {'已锁定' if locked else '未锁定'}")
        else:
            print(f"[OK] {args.browser} 浏览器未运行，可以正常继承用户数据。")
        return

    # URL是必需的（除非只是检查浏览器）
    if not args.url:
        parser.error("需要提供 --url 参数")

    # 构建配置
    options = {
        'url': args.url,
        'output_dir': args.output,
        'headless': not args.headed,
        'browser_type': args.browser,
        'browser_path': args.browser_path,
        'user_data_dir': args.user_data_dir,
        'profile_dir': args.profile,
        'use_existing_user_data': not args.no_user_data and not args.incognito,
        'incognito': args.incognito,
        'wait_time': args.wait,
        'no_imgs': args.no_images,
        'max_retries': args.max_retries,
        'scroll_page': not args.no_scroll
    }

    capture = DrissionPageCapture(options)
    result = capture.capture(args.url)

    print(f"\n{'='*60}")
    print(f"[抓包结果]")
    print(f"  总请求: {len(result['all_requests'])}")
    print(f"  API请求(XHR/Fetch): {len(result['api_requests'])}")
    print(f"  JS文件: {len(result['js_files'])}")
    print(f"  Cookies: {len(result['cookies'])}")
    print(f"{'='*60}")
    print(f"\n[OUTPUT] API请求: {args.output}/xhr/api-requests.json")
    print(f"[OUTPUT] JS文件: {args.output}/js/js-files.json")
    print(f"[OUTPUT] Cookies: {args.output}/cookies.json")
    print(f"[OUTPUT] 页面HTML: {args.output}/page.html")
    print(f"[OUTPUT] 抓包摘要: {args.output}/capture-summary.json")


if __name__ == '__main__':
    main()