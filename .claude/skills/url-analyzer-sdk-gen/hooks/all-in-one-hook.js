/**
 * 综合Hook脚本 - 包含所有常用的JavaScript Hook
 * 来源：https://spiderapi.cn/pages/js-hook/
 *
 * 使用方式：
 * 1. 浏览器控制台直接粘贴执行
 * 2. Playwright的page.addInitScript()注入
 * 3. 油猴插件自动注入
 *
 * 功能列表：
 * - Hook Cookie
 * - Hook Request Header
 * - Hook 无限Debugger
 * - Hook XHR
 * - Hook Fetch
 * - Hook JSON.stringify/parse
 * - Hook Function
 * - Hook WebSocket
 * - Hook String/Array方法
 * - Hook eval
 * - Hook 定时器
 * - Hook Canvas
 * - 固定随机变量
 */

(function() {
    'use strict';

    // ========== 全局配置 ==========
    const CONFIG = {
        debug: true,                    // 是否开启debugger
        logPrefix: '[Hook]',            // 日志前缀
        breakKeywords: ['sign', 'encrypt', 'token', 'secret'], // 触发debugger的关键词
        interceptData: []               // 拦截数据存储
    };

    // ========== 工具函数 ==========
    function log(...args) {
        console.log(CONFIG.logPrefix, ...args);
    }

    function shouldBreak(content) {
        if (typeof content !== 'string') return false;
        return CONFIG.breakKeywords.some(kw => content.toLowerCase().includes(kw));
    }

    function saveIntercept(type, data) {
        CONFIG.interceptData.push({
            type: type,
            data: data,
            timestamp: Date.now()
        });
    }

    // ========== 1. Hook Cookie ==========
    function hookCookie() {
        let cookieCache = "";
        try {
            Object.defineProperty(document, "cookie", {
                set: function(val) {
                    log("Cookie set =>", val);
                    if (shouldBreak(val)) {
                        log("检测到关键词，触发断点");
                        if (CONFIG.debug) debugger;
                    }
                    saveIntercept('cookie_set', val);
                    cookieCache = val;
                    return val;
                },
                get: function() {
                    return cookieCache;
                },
                configurable: true
            });
            log("✓ Cookie Hook 已启用");
        } catch(e) {
            log("✗ Cookie Hook 失败:", e.message);
        }
    }

    // ========== 2. Hook Request Header ==========
    function hookRequestHeader() {
        try {
            const headerCache = window.XMLHttpRequest.prototype.setRequestHeader;
            window.XMLHttpRequest.prototype.setRequestHeader = function(key, value) {
                log("RequestHeader set =>", key, "=", value);
                if (shouldBreak(key) || shouldBreak(String(value))) {
                    if (CONFIG.debug) debugger;
                }
                saveIntercept('header', {key, value});
                return headerCache.apply(this, arguments);
            };
            log("✓ Request Header Hook 已启用");
        } catch(e) {
            log("✗ Request Header Hook 失败:", e.message);
        }
    }

    // ========== 3. Hook 无限Debugger ==========
    function hookDebugger() {
        try {
            // 方法1: Hook constructor
            const constructorCache = Function.prototype.constructor;
            Function.prototype.constructor = function(string) {
                if (string === "debugger") {
                    log("拦截 debugger 构造");
                    return function() {};
                }
                return constructorCache.apply(this, arguments);
            };

            // 方法2: Hook eval中的debugger
            const evalCache = window.eval;
            window.eval = function(string) {
                if (typeof string === 'string' && string.includes('debugger')) {
                    log("拦截 eval 中的 debugger");
                    string = string.replace(/debugger/g, '');
                }
                return evalCache.call(this, string);
            };

            log("✓ 无限Debugger Hook 已启用");
        } catch(e) {
            log("✗ 无限Debugger Hook 失败:", e.message);
        }
    }

    // ========== 4. Hook XHR ==========
    function hookXHR() {
        try {
            const openCache = window.XMLHttpRequest.prototype.open;
            const sendCache = window.XMLHttpRequest.prototype.send;

            window.XMLHttpRequest.prototype.open = function(method, url) {
                log("XHR open =>", method, url);
                this._hookUrl = url;
                this._hookMethod = method;
                if (shouldBreak(url)) {
                    if (CONFIG.debug) debugger;
                }
                saveIntercept('xhr_open', {method, url});
                return openCache.apply(this, arguments);
            };

            window.XMLHttpRequest.prototype.send = function(data) {
                log("XHR send =>", this._hookUrl, data);
                if (data && shouldBreak(String(data))) {
                    if (CONFIG.debug) debugger;
                }
                saveIntercept('xhr_send', {url: this._hookUrl, data});

                // 监听响应
                this.addEventListener('load', function() {
                    log("XHR response =>", this._hookUrl, this.status);
                    saveIntercept('xhr_response', {
                        url: this._hookUrl,
                        status: this.status,
                        response: this.responseText.substring(0, 500)
                    });
                });

                return sendCache.apply(this, arguments);
            };

            log("✓ XHR Hook 已启用");
        } catch(e) {
            log("✗ XHR Hook 失败:", e.message);
        }
    }

    // ========== 5. Hook Fetch ==========
    function hookFetch() {
        try {
            const fetchCache = Object.getOwnPropertyDescriptor(window, "fetch");
            Object.defineProperty(window, "fetch", {
                value: function(url, options) {
                    log("Fetch =>", url, options);
                    if (shouldBreak(String(url)) || (options && shouldBreak(String(options.body)))) {
                        if (CONFIG.debug) debugger;
                    }
                    saveIntercept('fetch', {url, options});
                    return fetchCache.value.apply(this, arguments);
                },
                configurable: true
            });
            log("✓ Fetch Hook 已启用");
        } catch(e) {
            log("✗ Fetch Hook 失败:", e.message);
        }
    }

    // ========== 6. Hook JSON ==========
    function hookJSON() {
        try {
            const stringifyCache = JSON.stringify;
            const parseCache = JSON.parse;

            JSON.stringify = function(params) {
                log("JSON.stringify =>", typeof params === 'object' ? JSON.stringify(params).substring(0, 200) : params);
                if (params && shouldBreak(JSON.stringify(params))) {
                    if (CONFIG.debug) debugger;
                }
                saveIntercept('stringify', params);
                return stringifyCache.apply(this, arguments);
            };

            JSON.parse = function(params) {
                log("JSON.parse =>", typeof params === 'string' ? params.substring(0, 200) : params);
                if (params && shouldBreak(String(params))) {
                    if (CONFIG.debug) debugger;
                }
                const result = parseCache.apply(this, arguments);
                saveIntercept('parse', params);
                return result;
            };

            log("✓ JSON Hook 已启用");
        } catch(e) {
            log("✗ JSON Hook 失败:", e.message);
        }
    }

    // ========== 7. Hook Function ==========
    function hookFunction() {
        try {
            const FunctionCache = window.Function;
            window.Function = function() {
                const src = arguments[arguments.length - 1];
                log("Function =>", typeof src === 'string' ? src.substring(0, 200) : src);
                if (typeof src === 'string' && shouldBreak(src)) {
                    if (CONFIG.debug) debugger;
                }
                saveIntercept('function', src);
                return FunctionCache.apply(this, arguments);
            };
            window.Function.toString = function() {
                return FunctionCache.toString();
            };
            log("✓ Function Hook 已启用");
        } catch(e) {
            log("✗ Function Hook 失败:", e.message);
        }
    }

    // ========== 8. Hook WebSocket ==========
    function hookWebSocket() {
        try {
            const sendCache = WebSocket.prototype.send;
            WebSocket.prototype.send = function(data) {
                log("WebSocket send =>", data);
                if (shouldBreak(String(data))) {
                    if (CONFIG.debug) debugger;
                }
                saveIntercept('websocket', data);
                return sendCache.apply(this, arguments);
            };
            log("✓ WebSocket Hook 已启用");
        } catch(e) {
            log("✗ WebSocket Hook 失败:", e.message);
        }
    }

    // ========== 9. Hook String/Array方法 ==========
    function hookStringMethods() {
        try {
            // Hook split
            const splitCache = String.prototype.split;
            String.prototype.split = function(separator, limit) {
                log("String.split =>", this.substring(0, 100), separator);
                if (shouldBreak(this.toString())) {
                    if (CONFIG.debug) debugger;
                }
                return splitCache.apply(this, arguments);
            };

            // Hook charAt
            const charAtCache = String.prototype.charAt;
            String.prototype.charAt = function(index) {
                return charAtCache.apply(this, arguments);
            };

            log("✓ String方法 Hook 已启用");
        } catch(e) {
            log("✗ String方法 Hook 失败:", e.message);
        }
    }

    // ========== 10. Hook eval ==========
    function hookEval() {
        try {
            const evalCache = window.eval;
            window.eval = function(string) {
                log("eval =>", typeof string === 'string' ? string.substring(0, 200) : string);
                if (typeof string === 'string' && shouldBreak(string)) {
                    if (CONFIG.debug) debugger;
                }
                saveIntercept('eval', string);
                return evalCache.call(this, string);
            };
            window.eval.toString = function() {
                return evalCache.toString();
            };
            log("✓ eval Hook 已启用");
        } catch(e) {
            log("✗ eval Hook 失败:", e.message);
        }
    }

    // ========== 11. Hook 定时器 ==========
    function hookTimer() {
        try {
            const setIntervalCache = setInterval;
            const setTimeoutCache = setTimeout;

            setInterval = function(func, delay) {
                log("setInterval =>", delay + 'ms');
                saveIntercept('setInterval', {func: func.toString().substring(0, 100), delay});
                return setIntervalCache.apply(this, arguments);
            };

            setTimeout = function(func, delay) {
                log("setTimeout =>", delay + 'ms');
                saveIntercept('setTimeout', {func: func.toString().substring(0, 100), delay});
                return setTimeoutCache.apply(this, arguments);
            };

            log("✓ 定时器 Hook 已启用");
        } catch(e) {
            log("✗ 定时器 Hook 失败:", e.message);
        }
    }

    // ========== 12. Hook Canvas ==========
    function hookCanvas() {
        try {
            const createElementCache = document.createElement;
            document.createElement = function(tagName) {
                if (tagName.toLowerCase() === 'canvas') {
                    log("createElement => canvas");
                    saveIntercept('canvas', true);
                }
                return createElementCache.apply(this, arguments);
            };
            log("✓ Canvas Hook 已启用");
        } catch(e) {
            log("✗ Canvas Hook 失败:", e.message);
        }
    }

    // ========== 13. Hook 加密库 ==========
    function hookCrypto() {
        try {
            // CryptoJS MD5
            if (window.CryptoJS && CryptoJS.MD5) {
                const md5Cache = CryptoJS.MD5;
                CryptoJS.MD5 = function(message) {
                    log("CryptoJS.MD5 =>", message.toString().substring(0, 100));
                    saveIntercept('md5', {input: message.toString(), output: md5Cache.apply(this, arguments).toString()});
                    if (CONFIG.debug) debugger;
                    return md5Cache.apply(this, arguments);
                };
            }

            // CryptoJS SHA256
            if (window.CryptoJS && CryptoJS.SHA256) {
                const sha256Cache = CryptoJS.SHA256;
                CryptoJS.SHA256 = function(message) {
                    log("CryptoJS.SHA256 =>", message.toString().substring(0, 100));
                    saveIntercept('sha256', {input: message.toString(), output: sha256Cache.apply(this, arguments).toString()});
                    if (CONFIG.debug) debugger;
                    return sha256Cache.apply(this, arguments);
                };
            }

            // Base64 btoa
            const btoaCache = window.btoa;
            window.btoa = function(str) {
                log("btoa =>", str.substring(0, 100));
                saveIntercept('btoa', {input: str, output: btoaCache.apply(this, arguments)});
                return btoaCache.apply(this, arguments);
            };

            // Base64 atob
            const atobCache = window.atob;
            window.atob = function(str) {
                log("atob =>", str.substring(0, 100));
                saveIntercept('atob', {input: str, output: atobCache.apply(this, arguments)});
                return atobCache.apply(this, arguments);
            };

            log("✓ 加密库 Hook 已启用");
        } catch(e) {
            log("✗ 加密库 Hook 失败:", e.message);
        }
    }

    // ========== 14. Hook onbeforeunload ==========
    function hookBeforeUnload() {
        try {
            window.onbeforeunload = function() {
                log("onbeforeunload 被阻止");
                return false;
            };
            log("✓ onbeforeunload Hook 已启用");
        } catch(e) {
            log("✗ onbeforeunload Hook 失败:", e.message);
        }
    }

    // ========== 15. 固定随机变量 ==========
    function fixRandom(fixedTimestamp = null) {
        try {
            const timestamp = fixedTimestamp || Date.now();

            Date.now = function() { return timestamp; };
            Date.parse = function() { return timestamp; };
            Date.prototype.valueOf = function() { return timestamp; };
            Date.prototype.getTime = function() { return timestamp; };

            Math.random = function() { return 0.123456789; };

            if (window.crypto && window.crypto.getRandomValues) {
                window.crypto.getRandomValues = function(array) {
                    return array;
                };
            }

            log("✓ 随机变量已固定为:", timestamp);
        } catch(e) {
            log("✗ 固定随机变量失败:", e.message);
        }
    }

    // ========== 清除定时器 ==========
    function clearAllTimers() {
        for (let i = 1; i < 99999; i++) {
            window.clearInterval(i);
            window.clearTimeout(i);
        }
        log("已清除所有定时器");
    }

    // ========== 导出函数 ==========
    window.__hook_config__ = CONFIG;
    window.__hook_export__ = function() {
        return CONFIG.interceptData;
    };
    window.__hook_clear__ = function() {
        CONFIG.interceptData = [];
        log("拦截数据已清空");
    };
    window.__hook_set_debug__ = function(enabled) {
        CONFIG.debug = enabled;
        log("Debug模式:", enabled ? "开启" : "关闭");
    };
    window.__fix_random__ = fixRandom;
    window.__clear_timers__ = clearAllTimers;

    // ========== 初始化所有Hook ==========
    function init() {
        log("========== 开始初始化Hook ==========");
        hookCookie();
        hookRequestHeader();
        hookDebugger();
        hookXHR();
        hookFetch();
        hookJSON();
        hookFunction();
        hookWebSocket();
        hookStringMethods();
        hookEval();
        hookTimer();
        hookCanvas();
        hookCrypto();
        hookBeforeUnload();
        log("========== Hook初始化完成 ==========");
        log("可用命令:");
        log("  __hook_export__()      - 导出拦截数据");
        log("  __hook_clear__()       - 清空拦截数据");
        log("  __hook_set_debug__(bool) - 开关debugger");
        log("  __fix_random__(timestamp) - 固定随机变量");
        log("  __clear_timers__()     - 清除所有定时器");
    }

    init();
})();