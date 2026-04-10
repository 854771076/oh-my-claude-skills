/**
 * Playwright网络抓包脚本 V2.1
 * 抓取页面加载过程中的所有网络请求，保存为HAR格式并提取关键信息
 *
 * 使用方式:
 * node playwright-capture.js <URL> [output-dir] [options]
 *
 * 选项:
 *   --headless        无头模式运行 (默认: true)
 *   --headed          有头模式运行 (显示浏览器)
 *   --browser <type>  浏览器类型: chromium, chrome, edge, firefox (默认: chromium)
 *   --chrome-path     Chrome可执行文件路径
 *   --edge-path       Edge可执行文件路径
 *   --user-data-dir   自定义用户数据目录路径
 *   --profile         Profile目录名 (默认: Default)
 *   --no-user-data    不继承用户数据，使用全新会话
 *
 * 用户数据继承说明:
 *   使用 chrome/edge 浏览器时，默认自动检测并继承本地浏览器的用户数据
 *   (包括Cookies、登录状态、历史记录等)，实现免登录抓包
 *
 * 示例:
 *   node playwright-capture.js "https://example.com"
 *   node playwright-capture.js "https://example.com" "./output" --headed
 *   node playwright-capture.js "https://example.com" "./output" --browser chrome
 *   node playwright-capture.js "https://example.com" "./output" --browser chrome --profile "Profile 1"
 *   node playwright-capture.js "https://example.com" "./output" --browser chrome --no-user-data
 */

const { chromium, firefox } = require('playwright');
const fs = require('fs');
const path = require('path');

// 默认浏览器路径配置
const DEFAULT_BROWSER_PATHS = {
    chrome: {
        win32: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        win64: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
        darwin: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        linux: '/usr/bin/google-chrome'
    },
    edge: {
        win32: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
        win64: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
        darwin: '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        linux: '/usr/bin/microsoft-edge'
    }
};

// 默认用户数据目录配置
const DEFAULT_USER_DATA_DIRS = {
    chrome: {
        win32: 'C:/Users/{username}/AppData/Local/Google/Chrome/User Data',
        darwin: '/Users/{username}/Library/Application Support/Google/Chrome',
        linux: '/home/{username}/.config/google-chrome'
    },
    edge: {
        win32: 'C:/Users/{username}/AppData/Local/Microsoft/Edge/User Data',
        darwin: '/Users/{username}/Library/Application Support/Microsoft Edge',
        linux: '/home/{username}/.config/microsoft-edge'
    }
};

class NetworkCapture {
    constructor(options = {}) {
        this.url = options.url;
        this.outputDir = options.outputDir || './capture-output';
        this.headless = options.headless !== false; // 默认无头
        this.browserType = options.browserType || 'chromium';
        this.browserPath = options.browserPath;
        this.userDataDir = options.userDataDir; // 用户数据目录
        this.useExistingUserData = options.useExistingUserData !== false; // 默认使用已有用户数据
        this.profileDir = options.profileDir || 'Default'; // Chrome/Edge profile目录名
        this.apiRequests = [];
        this.jsFiles = [];
        this.allRequests = [];
    }

    /**
     * 获取本地浏览器路径
     */
    getLocalBrowserPath(browserType) {
        if (this.browserPath) return this.browserPath;

        const platform = process.platform;
        const arch = process.arch;
        const paths = DEFAULT_BROWSER_PATHS[browserType];

        if (!paths) return null;

        // 尝试不同的路径
        for (const key of [platform + arch, platform, 'win64', 'win32']) {
            if (paths[key] && fs.existsSync(paths[key])) {
                return paths[key];
            }
        }

        return null;
    }

    /**
     * 获取浏览器用户数据目录
     */
    getUserDataDir(browserType) {
        if (this.userDataDir) return this.userDataDir;

        if (!this.useExistingUserData) return null;

        const platform = process.platform;
        const username = process.env.USERNAME || process.env.USER || 'Default';
        const paths = DEFAULT_USER_DATA_DIRS[browserType];

        if (!paths) return null;

        // 尝试不同的路径
        for (const key of [platform, 'win32']) {
            if (paths[key]) {
                let path = paths[key].replace('{username}', username);
                if (fs.existsSync(path)) {
                    return path;
                }
            }
        }

        return null;
    }

    /**
     * 启动浏览器
     * @returns {Object} 包含 browser 和 context 的对象
     */
    async launchBrowser() {
        const launchOptions = {
            headless: this.headless
        };

        let browser;
        let context;
        let usePersistentContext = false;

        // 检查是否使用本地浏览器并继承用户数据
        if (this.browserType === 'chrome' || this.browserType === 'edge') {
            const browserPath = this.getLocalBrowserPath(this.browserType);
            const userDataDir = this.getUserDataDir(this.browserType);

            if (browserPath) {
                launchOptions.executablePath = browserPath;
                console.log(`[INFO] 使用本地${this.browserType === 'chrome' ? 'Chrome' : 'Edge'}: ${browserPath}`);
            } else {
                console.log(`[WARN] 未找到本地${this.browserType === 'chrome' ? 'Chrome' : 'Edge'}，使用Chromium`);
            }

            // 如果找到了用户数据目录，使用持久化上下文
            if (userDataDir && this.useExistingUserData) {
                usePersistentContext = true;
                launchOptions.userDataDir = userDataDir;
                launchOptions.args = [
                    `--profile-directory=${this.profileDir}`,  // 指定profile
                    '--disable-blink-features=AutomationControlled',  // 防止被检测为自动化
                ];
                console.log(`[INFO] 使用用户数据目录: ${userDataDir}`);
                console.log(`[INFO] Profile: ${this.profileDir}`);

                // 使用持久化上下文启动
                context = await chromium.launchPersistentContext(userDataDir, launchOptions);
                browser = null;  // 持久化上下文不需要单独的browser对象
            } else if (browserPath) {
                browser = await chromium.launch(launchOptions);
            } else {
                browser = await chromium.launch({ headless: this.headless });
            }
        } else if (this.browserType === 'firefox') {
            browser = await firefox.launch(launchOptions);
            console.log('[INFO] 使用Firefox');
        } else {
            // Chromium 默认不使用用户数据
            browser = await chromium.launch(launchOptions);
            console.log('[INFO] 使用Chromium (自动下载)');
        }

        console.log(`[INFO] 浏览器模式: ${this.headless ? '无头' : '有头'}`);
        console.log(`[INFO] 上下文类型: ${usePersistentContext ? '持久化(继承用户数据)' : '临时(全新会话)'}`);

        return { browser, context, usePersistentContext };
    }

    async capture() {
        // 确保输出目录存在
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }

        const { browser, context: persistentContext, usePersistentContext } = await this.launchBrowser();

        // 根据上下文类型获取context和page
        let context, page;
        if (usePersistentContext && persistentContext) {
            context = persistentContext;
            page = context.pages()[0] || await context.newPage();
        } else {
            context = await browser.newContext();
            page = await context.newPage();
        }

        // 监听所有网络请求
        page.on('request', request => {
            this.allRequests.push({
                url: request.url(),
                method: request.method(),
                headers: request.headers(),
                postData: request.postData(),
                resourceType: request.resourceType()
            });

            // 提取JS文件
            if (request.resourceType() === 'script') {
                this.jsFiles.push({
                    url: request.url(),
                    type: 'external'
                });
            }

            // 提取API请求（XHR/Fetch）
            if (request.resourceType() === 'xhr' || request.resourceType() === 'fetch') {
                this.apiRequests.push({
                    url: request.url(),
                    method: request.method(),
                    headers: request.headers(),
                    postData: request.postData(),
                    resourceType: request.resourceType()
                });
            }
        });

        // 监听响应
        page.on('response', async response => {
            const request = response.request();

            // 为API请求添加响应信息
            if (request.resourceType() === 'xhr' || request.resourceType() === 'fetch') {
                const index = this.apiRequests.findIndex(r => r.url === request.url());
                if (index !== -1) {
                    try {
                        const body = await response.text();
                        this.apiRequests[index].response = {
                            status: response.status(),
                            headers: response.headers(),
                            body: body.substring(0, 5000) // 截取前5000字符避免过大
                        };
                    } catch (e) {
                        // 某些响应可能无法读取
                        this.apiRequests[index].response = {
                            status: response.status(),
                            headers: response.headers(),
                            error: 'Unable to read response body'
                        };
                    }
                }
            }
        });

        try {
            // 访问页面并等待网络稳定
            console.log(`[INFO] 正在访问: ${this.url}`);

            await page.goto(this.url, {
                waitUntil: 'networkidle', // 等待网络空闲
                timeout: 30000
            });

            // 等待额外时间确保所有XHR完成
            await page.waitForTimeout(3000);

            // 检查是否有内联JS
            const inlineScripts = await page.evaluate(() => {
                const scripts = document.querySelectorAll('script:not([src])');
                return Array.from(scripts).map(s => ({
                    content: s.textContent.substring(0, 2000),
                    type: 'inline'
                }));
            });
            this.jsFiles.push(...inlineScripts);

            // 获取页面基本信息
            const pageInfo = await page.evaluate(() => {
                return {
                    title: document.title,
                    url: window.location.href,
                    html: document.documentElement.outerHTML
                };
            });
            this.pageInfo = pageInfo;

            // 获取Cookies
            this.cookies = await context.cookies();
            console.log(`[INFO] 获取到 ${this.cookies.length} 个Cookies`);

            console.log(`[SUCCESS] 页面加载完成`);
            console.log(`[INFO] 捕获请求总数: ${this.allRequests.length}`);
            console.log(`[INFO] API请求数: ${this.apiRequests.length}`);
            console.log(`[INFO] JS文件数: ${this.jsFiles.length}`);

        } catch (error) {
            console.error(`[ERROR] 页面加载失败: ${error.message}`);
            throw error;
        } finally {
            // 关闭上下文
            await context.close();
            // 持久化上下文模式下browser为null，需要通过context.close()关闭
            if (browser) {
                await browser.close();
            }
        }

        // 保存提取的数据
        this._saveExtractedData();

        return {
            apiRequests: this.apiRequests,
            jsFiles: this.jsFiles,
            allRequests: this.allRequests
        };
    }

    _saveExtractedData() {
        // 创建子目录以匹配DrissionPage结构
        const xhrDir = path.join(this.outputDir, 'xhr');
        const jsDir = path.join(this.outputDir, 'js');

        if (!fs.existsSync(xhrDir)) {
            fs.mkdirSync(xhrDir, { recursive: true });
        }
        if (!fs.existsSync(jsDir)) {
            fs.mkdirSync(jsDir, { recursive: true });
        }

        // 保存API请求详情（兼容两种路径）
        fs.writeFileSync(
            path.join(this.outputDir, 'api-requests.json'),
            JSON.stringify(this.apiRequests, null, 2)
        );
        fs.writeFileSync(
            path.join(xhrDir, 'api-requests.json'),
            JSON.stringify(this.apiRequests, null, 2)
        );

        // 保存JS文件列表（兼容两种路径）
        fs.writeFileSync(
            path.join(this.outputDir, 'js-files.json'),
            JSON.stringify(this.jsFiles, null, 2)
        );
        fs.writeFileSync(
            path.join(jsDir, 'js-files.json'),
            JSON.stringify(this.jsFiles, null, 2)
        );

        // 保存完整请求列表
        fs.writeFileSync(
            path.join(this.outputDir, 'all-requests.json'),
            JSON.stringify(this.allRequests, null, 2)
        );

        // 保存Cookies
        if (this.cookies) {
            fs.writeFileSync(
                path.join(this.outputDir, 'cookies.json'),
                JSON.stringify(this.cookies, null, 2)
            );
        }

        // 保存页面HTML
        if (this.pageInfo && this.pageInfo.html) {
            fs.writeFileSync(
                path.join(this.outputDir, 'page.html'),
                this.pageInfo.html
            );
        }

        // 保存抓包摘要
        const summary = {
            url: this.url,
            capture_time: new Date().toISOString(),
            total_requests: this.allRequests.length,
            api_requests: this.apiRequests.length,
            js_files: this.jsFiles.length,
            cookies_count: this.cookies ? this.cookies.length : 0
        };
        fs.writeFileSync(
            path.join(this.outputDir, 'capture-summary.json'),
            JSON.stringify(summary, null, 2)
        );

        console.log(`[INFO] 数据已保存到: ${this.outputDir}`);
    }
}

// 解析命令行参数
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        url: null,
        outputDir: './capture-output',
        headless: true,
        browserType: 'chromium',
        browserPath: null,
        userDataDir: null,
        useExistingUserData: true,  // 默认使用已有用户数据
        profileDir: 'Default'       // 默认profile
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        if (arg.startsWith('--')) {
            switch (arg) {
                case '--headless':
                    options.headless = true;
                    break;
                case '--headed':
                    options.headless = false;
                    break;
                case '--browser':
                    options.browserType = args[++i];
                    break;
                case '--chrome-path':
                    options.browserPath = args[++i];
                    options.browserType = 'chrome';
                    break;
                case '--edge-path':
                    options.browserPath = args[++i];
                    options.browserType = 'edge';
                    break;
                case '--user-data-dir':
                    options.userDataDir = args[++i];
                    break;
                case '--profile':
                    options.profileDir = args[++i];
                    break;
                case '--no-user-data':
                    options.useExistingUserData = false;
                    break;
                case '--help':
                case '-h':
                    console.log(`
Playwright网络抓包脚本 V2.1

使用方式:
  node playwright-capture.js <URL> [output-dir] [options]

选项:
  --headless            无头模式运行 (默认)
  --headed              有头模式运行 (显示浏览器窗口)
  --browser <type>      浏览器类型: chromium, chrome, edge, firefox
  --chrome-path         Chrome可执行文件路径
  --edge-path           Edge可执行文件路径
  --user-data-dir       自定义用户数据目录路径
  --profile             Profile目录名 (默认: Default)
  --no-user-data        不使用已有用户数据，创建全新会话

用户数据继承说明:
  使用 chrome/edge 浏览器时，默认自动检测并继承本地浏览器的用户数据
  (包括Cookies、登录状态、历史记录等)，实现免登录抓包
  使用 --user-data-dir 可指定自定义用户数据目录
  使用 --no-user-data 可禁用用户数据继承，使用全新会话

示例:
  node playwright-capture.js "https://example.com"
  node playwright-capture.js "https://example.com" "./output" --headed
  node playwright-capture.js "https://example.com" "./output" --browser chrome
  node playwright-capture.js "https://example.com" "./output" --browser chrome --profile "Profile 1"
  node playwright-capture.js "https://example.com" "./output" --browser chrome --no-user-data
                    `);
                    process.exit(0);
                    break;
            }
        } else if (!arg.startsWith('-')) {
            if (!options.url) {
                options.url = arg;
            } else {
                options.outputDir = arg;
            }
        }
    }

    return options;
}

// 命令行入口
async function main() {
    const options = parseArgs();

    if (!options.url) {
        console.log('Usage: node playwright-capture.js <URL> [output-dir] [options]');
        console.log('');
        console.log('Options:');
        console.log('  --headless            无头模式运行 (默认)');
        console.log('  --headed              有头模式运行');
        console.log('  --browser <type>      浏览器类型: chromium, chrome, edge, firefox');
        console.log('  --user-data-dir       自定义用户数据目录');
        console.log('  --profile             Profile目录名 (默认: Default)');
        console.log('  --no-user-data        不继承用户数据，全新会话');
        console.log('');
        console.log('Example:');
        console.log('  node playwright-capture.js "https://example.com"');
        console.log('  node playwright-capture.js "https://example.com" "./output" --browser chrome');
        console.log('  node playwright-capture.js "https://example.com" "./output" --browser chrome --profile "Profile 1"');
        console.log('  node playwright-capture.js "https://example.com" "./output" --headed --browser chrome');
        process.exit(1);
    }

    const capture = new NetworkCapture(options);

    try {
        const result = await capture.capture();
        console.log('\n[OUTPUT FILES]:');
        console.log(`  API请求: ${path.join(options.outputDir, 'api-requests.json')}`);
        console.log(`  JS文件: ${path.join(options.outputDir, 'js-files.json')}`);
        console.log(`  全部请求: ${path.join(options.outputDir, 'all-requests.json')}`);
    } catch (error) {
        console.error('\n[FATAL] 抓包失败:', error.message);
        process.exit(1);
    }
}

main();

// 导出类供其他脚本使用
module.exports = NetworkCapture;