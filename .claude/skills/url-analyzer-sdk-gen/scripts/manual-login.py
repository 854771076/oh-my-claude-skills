#!/usr/bin/env python3
"""
手动登录脚本 - 打开浏览器让用户手动登录网站
登录完成后关闭浏览器即可

使用方式:
python manual-login.py --url "https://www.bilibili.com/" --browser chrome
"""

import os
import sys
import json
import time
import argparse
import platform
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    print("[ERROR] 请先安装DrissionPage: pip install DrissionPage")
    sys.exit(1)


def get_browser_paths():
    """获取浏览器路径"""
    return {
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


def check_browser_running(browser_type: str) -> bool:
    """检查浏览器是否正在运行"""
    process_names = {
        'chrome': ['chrome.exe', 'chrome'],
        'edge': ['msedge.exe', 'msedge']
    }

    system = platform.system()
    names = process_names.get(browser_type, [])

    try:
        if system == 'Windows':
            result = subprocess.run(['tasklist'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for proc in names:
                if proc.lower() in result.stdout.lower():
                    return True
    except Exception:
        pass

    return False


def manual_login(url: str, browser_type: str, user_data_dir: str, headless: bool = False):
    """
    打开浏览器进行手动登录

    Args:
        url: 目标网站URL
        browser_type: 浏览器类型 (chrome/edge)
        user_data_dir: 用户数据目录（项目内的目录）
        headless: 是否无头模式（登录时应该为False）
    """
    system = platform.system()
    browser_paths = get_browser_paths()

    # 创建ChromiumOptions
    co = ChromiumOptions()

    # 设置浏览器路径
    if browser_type in browser_paths and system in browser_paths[browser_type]:
        browser_path = browser_paths[browser_type][system]
        if os.path.exists(browser_path):
            co.set_browser_path(browser_path)

    # 设置用户数据目录（项目内）
    co.set_user_data_path(user_data_dir)
    # co.auto_port()

    # 显示浏览器窗口
    if headless:
        co.headless(True)

    # 防止被检测
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--window-size=1280,800')

    print(f"\n{'='*60}")
    print(f"[手动登录模式]")
    print(f"目标网站: {url}")
    print(f"浏览器: {browser_type}")
    print(f"用户数据目录: {user_data_dir}")
    print(f"{'='*60}")
    print(f"\n请在浏览器中完成登录操作。")
    print(f"登录完成后，关闭浏览器窗口或按 Ctrl+C 退出。\n")

    # 创建页面
    page = ChromiumPage(co)

    try:
        # 访问目标网站
        page.get(url)

        # 等待用户操作
        print("浏览器已打开，等待您登录...")
        print("登录完成后，请关闭浏览器窗口。")

        # 保持浏览器打开，等待用户关闭
        while True:
            time.sleep(1)
            # 检查页面是否还存在
            try:
                _ = page.url
            except:
                print("\n浏览器已关闭。")
                break

    except KeyboardInterrupt:
        print("\n\n用户中断，正在关闭浏览器...")
    finally:
        try:
            page.quit()
        except:
            pass

    # 保存登录状态信息
    login_info = {
        'url': url,
        'browser': browser_type,
        'user_data_dir': user_data_dir,
        'login_time': datetime.now().isoformat(),
        'status': 'completed'
    }

    info_file = Path(user_data_dir) / 'login_info.json'
    info_file.parent.mkdir(parents=True, exist_ok=True)
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(login_info, f, indent=2, ensure_ascii=False)

    print(f"\n登录信息已保存到: {info_file}")
    print("后续抓包将自动使用此登录状态。")


def main():
    parser = argparse.ArgumentParser(
        description='手动登录脚本 - 在浏览器中手动登录网站',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python manual-login.py --url "https://www.bilibili.com/" --browser chrome
  python manual-login.py --url "https://www.bilibili.com/" --browser edge --user-data-dir "./browser-data"
        '''
    )

    parser.add_argument('--url', '-u', required=True, help='目标网站URL')
    parser.add_argument('--browser', '-b', choices=['chrome', 'edge'], default='chrome', help='浏览器类型')
    parser.add_argument('--user-data-dir', '-d', default='./browser-data', help='用户数据目录')

    args = parser.parse_args()

    # 检查浏览器是否运行
    if check_browser_running(args.browser):
        print(f"[警告] {args.browser} 浏览器正在运行！")
        print("建议先关闭浏览器，以确保用户数据目录不被锁定。")
        print("按 Enter 继续，或按 Ctrl+C 取消...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n已取消。")
            return

    manual_login(args.url, args.browser, args.user_data_dir)


if __name__ == '__main__':
    main()