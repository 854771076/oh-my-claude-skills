/**
 * XHR Hook V2.0 - 拦截所有XMLHttpRequest请求
 * 用于记录请求参数、响应数据、调用栈
 *
 * 兼容性：ES5+（支持IE9+）
 *
 * 使用方式：
 * 1. 在浏览器控制台直接粘贴执行
 * 2. 或通过Playwright的page.evaluate()注入
 * 3. 通过油猴插件自动注入
 *
 * 输出：
 * - 请求URL、方法、参数
 * - 响应数据
 * - 完整调用栈
 */

(function() {
    'use strict';

    // ES5兼容性检查
    if (typeof XMLHttpRequest === 'undefined') {
        console.log('[XHR Hook] XMLHttpRequest 不存在，跳过Hook');
        return;
    }

    console.log('[XHR Hook] 开始拦截XHR请求...');

    // 存储拦截数据
    if (!window.__xhr_intercept_data__) {
        window.__xhr_intercept_data__ = [];
    }

    // 配置选项
    var CONFIG = {
        maxResponseLength: 5000,    // 最大响应长度
        logRequests: true,          // 是否打印请求日志
        logResponses: true,         // 是否打印响应日志
        logStackTrace: true,        // 是否打印调用栈
        breakOnKeywords: [],        // 触发断点的关键词列表
        filterUrls: []              // 过滤的URL模式（不拦截）
    };

    // 保存原始方法
    var originalOpen = XMLHttpRequest.prototype.open;
    var originalSend = XMLHttpRequest.prototype.send;
    var originalSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;

    // 工具函数：检查是否包含关键词
    function containsKeyword(str, keywords) {
        if (!str || !keywords || keywords.length === 0) return false;
        var lowerStr = String(str).toLowerCase();
        for (var i = 0; i < keywords.length; i++) {
            if (lowerStr.indexOf(keywords[i].toLowerCase()) !== -1) {
                return true;
            }
        }
        return false;
    }

    // 工具函数：截断字符串
    function truncate(str, maxLength) {
        if (!str) return '';
        str = String(str);
        return str.length > maxLength ? str.substring(0, maxLength) : str;
    }

    // 工具函数：获取调用栈
    function getStackTrace() {
        try {
            throw new Error('Stack trace');
        } catch (e) {
            return e.stack || 'No stack trace available';
        }
    }

    // 工具函数：检查URL是否被过滤
    function isUrlFiltered(url) {
        if (!CONFIG.filterUrls || CONFIG.filterUrls.length === 0) return false;
        for (var i = 0; i < CONFIG.filterUrls.length; i++) {
            if (url.indexOf(CONFIG.filterUrls[i]) !== -1) {
                return true;
            }
        }
        return false;
    }

    // 重写open方法
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        var self = this;

        // 检查是否过滤
        if (isUrlFiltered(url)) {
            return originalOpen.apply(this, arguments);
        }

        // 初始化请求数据
        self.__xhr_data__ = {
            method: method,
            url: url,
            async: async,
            headers: {},
            startTime: Date.now(),
            endTime: null,
            duration: null,
            status: null,
            responseText: null,
            postData: null,
            callStack: null,
            error: null
        };

        if (CONFIG.logRequests) {
            console.log('[XHR Hook] open: ' + method + ' ' + url);
        }

        // 检查关键词断点
        if (containsKeyword(url, CONFIG.breakOnKeywords)) {
            console.log('[XHR Hook] 检测到关键词，触发断点: ' + url);
            debugger;
        }

        return originalOpen.apply(this, arguments);
    };

    // 重写setRequestHeader方法
    XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
        var self = this;

        if (self.__xhr_data__) {
            self.__xhr_data__.headers[header] = value;
        }

        return originalSetRequestHeader.apply(this, arguments);
    };

    // 重写send方法
    XMLHttpRequest.prototype.send = function(data) {
        var self = this;

        if (self.__xhr_data__) {
            self.__xhr_data__.postData = data;

            if (CONFIG.logRequests) {
                console.log('[XHR Hook] send: ' + self.__xhr_data__.url);
                if (data) {
                    console.log('[XHR Hook] 请求参数:', truncate(data, 500));
                }
            }

            // 获取调用栈
            if (CONFIG.logStackTrace) {
                self.__xhr_data__.callStack = getStackTrace();
            }

            // 检查关键词断点
            if (containsKeyword(String(data), CONFIG.breakOnKeywords)) {
                console.log('[XHR Hook] 请求体检测到关键词，触发断点');
                debugger;
            }
        }

        // 监听响应
        self.addEventListener('load', function() {
            if (self.__xhr_data__) {
                self.__xhr_data__.status = self.status;
                self.__xhr_data__.responseText = truncate(self.responseText, CONFIG.maxResponseLength);
                self.__xhr_data__.endTime = Date.now();
                self.__xhr_data__.duration = self.__xhr_data__.endTime - self.__xhr_data__.startTime;

                if (CONFIG.logResponses) {
                    console.log('[XHR Hook] 响应: ' + self.status + ' (' + self.__xhr_data__.duration + 'ms)');
                    console.log('[XHR Hook] 响应数据:', truncate(self.responseText, 500));
                }

                // 保存拦截数据
                window.__xhr_intercept_data__.push(self.__xhr_data__);

                // 定期输出统计
                if (window.__xhr_intercept_data__.length % 10 === 0) {
                    console.log('[XHR Hook] 已拦截 ' + window.__xhr_intercept_data__.length + ' 个请求');
                }
            }
        });

        // 监听错误
        self.addEventListener('error', function() {
            if (self.__xhr_data__) {
                self.__xhr_data__.error = true;
                console.error('[XHR Hook] 请求失败:', self.__xhr_data__.url);
            }
        });

        // 监听超时
        self.addEventListener('timeout', function() {
            if (self.__xhr_data__) {
                self.__xhr_data__.timeout = true;
                console.warn('[XHR Hook] 请求超时:', self.__xhr_data__.url);
            }
        });

        return originalSend.apply(this, arguments);
    };

    // ========== 导出函数 ==========

    // 导出拦截数据
    window.__export_xhr_data__ = function() {
        console.log(JSON.stringify(window.__xhr_intercept_data__, null, 2));
        return window.__xhr_intercept_data__;
    };

    // 清空拦截数据
    window.__clear_xhr_data__ = function() {
        window.__xhr_intercept_data__ = [];
        console.log('[XHR Hook] 数据已清空');
    };

    // 获取拦截统计
    window.__xhr_stats__ = function() {
        var data = window.__xhr_intercept_data__;
        var stats = {
            total: data.length,
            byMethod: {},
            byStatus: {},
            errors: 0,
            timeouts: 0
        };

        for (var i = 0; i < data.length; i++) {
            var item = data[i];
            stats.byMethod[item.method] = (stats.byMethod[item.method] || 0) + 1;
            stats.byStatus[item.status] = (stats.byStatus[item.status] || 0) + 1;
            if (item.error) stats.errors++;
            if (item.timeout) stats.timeouts++;
        }

        console.log('[XHR Hook] 统计信息:', stats);
        return stats;
    };

    // 配置Hook
    window.__xhr_config__ = function(options) {
        for (var key in options) {
            if (options.hasOwnProperty(key) && CONFIG.hasOwnProperty(key)) {
                CONFIG[key] = options[key];
            }
        }
        console.log('[XHR Hook] 配置已更新:', CONFIG);
    };

    // 获取当前配置
    window.__get_xhr_config__ = function() {
        return CONFIG;
    };

    console.log('[XHR Hook] 拦截已启用');
    console.log('[XHR Hook] 可用命令:');
    console.log('  __export_xhr_data__()  - 导出拦截数据');
    console.log('  __clear_xhr_data__()   - 清空拦截数据');
    console.log('  __xhr_stats__()        - 获取统计信息');
    console.log('  __xhr_config__(opts)   - 配置Hook选项');
})();