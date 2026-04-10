/**
 * Debug Hook - 调试辅助工具
 * 用于在关键位置设置断点、监控变量变化
 *
 * 使用方式：
 * 1. 在浏览器控制台直接粘贴执行
 * 2. 或通过Playwright的page.evaluate()注入
 */

(function() {
    console.log('[Debug Hook] 调试辅助工具已加载');

    // ========== 全局调试配置 ==========
    window.__debug_config__ = {
        breakpoints: [],
        watchVars: {},
        logs: []
    };

    // ========== 函数断点工具 ==========

    /**
     * 在指定函数入口设置断点
     * @param {string} funcName - 函数名
     * @param {object} context - 上下文对象（默认window）
     */
    window.__set_breakpoint__ = function(funcName, context = window) {
        if (typeof context[funcName] !== 'function') {
            console.error(`[Debug Hook] 函数不存在: ${funcName}`);
            return false;
        }

        const original = context[funcName];
        context[funcName] = function(...args) {
            console.log(`[Breakpoint] ${funcName} 被调用`);
            console.log('参数:', args);
            console.trace('调用栈');

            // 触发debugger
            debugger;

            return original.apply(this, args);
        };

        context[funcName].__original__ = original;
        window.__debug_config__.breakpoints.push({ funcName, context });

        console.log(`[Debug Hook] 断点已设置: ${funcName}`);
        return true;
    };

    /**
     * 移除断点
     * @param {string} funcName - 函数名
     */
    window.__remove_breakpoint__ = function(funcName) {
        const bp = window.__debug_config__.breakpoints.find(b => b.funcName === funcName);
        if (bp) {
            bp.context[funcName] = bp.context[funcName].__original__;
            window.__debug_config__.breakpoints = window.__debug_config__.breakpoints.filter(b => b.funcName !== funcName);
            console.log(`[Debug Hook] 断点已移除: ${funcName}`);
        }
    };

    // ========== 变量监控工具 ==========

    /**
     * 监控变量变化
     * @param {string} varName - 变量名
     * @param {object} context - 上下文对象
     */
    window.__watch_var__ = function(varName, context = window) {
        let value = context[varName];

        Object.defineProperty(context, varName, {
            get: function() {
                return value;
            },
            set: function(newValue) {
                const oldValue = value;
                value = newValue;

                const log = {
                    varName: varName,
                    oldValue: oldValue,
                    newValue: newValue,
                    timestamp: Date.now(),
                    stack: new Error().stack
                };

                window.__debug_config__.logs.push(log);
                console.log(`[Watch] ${varName} 已变化:`);
                console.log('  旧值:', oldValue);
                console.log('  新值:', newValue);
                console.trace('调用栈');

                // 触发debugger
                debugger;
            },
            configurable: true
        });

        window.__debug_config__.watchVars[varName] = true;
        console.log(`[Debug Hook] 变量已监控: ${varName}`);
    };

    // ========== 条件断点 ==========

    /**
     * 设置条件断点
     * @param {string} funcName - 函数名
     * @param {function} condition - 条件函数，返回true时触发断点
     * @param {object} context - 上下文
     */
    window.__set_conditional_breakpoint__ = function(funcName, condition, context = window) {
        if (typeof context[funcName] !== 'function') {
            console.error(`[Debug Hook] 函数不存在: ${funcName}`);
            return false;
        }

        const original = context[funcName];
        context[funcName] = function(...args) {
            try {
                if (condition.apply(this, args)) {
                    console.log(`[Conditional Breakpoint] ${funcName} 条件满足`);
                    console.log('参数:', args);
                    console.trace('调用栈');
                    debugger;
                }
            } catch (e) {
                console.error('[Debug Hook] 条件执行错误:', e);
            }

            return original.apply(this, args);
        };

        context[funcName].__original__ = original;
        console.log(`[Debug Hook] 条件断点已设置: ${funcName}`);
        return true;
    };

    // ========== 搜索函数定义 ==========

    /**
     * 在页面脚本中搜索函数定义
     * @param {string} keyword - 关键词
     */
    window.__search_function__ = function(keyword) {
        const scripts = document.getElementsByTagName('script');
        const results = [];

        for (let i = 0; i < scripts.length; i++) {
            const script = scripts[i];
            const content = script.textContent || '';
            const src = script.src || `inline script ${i}`;

            // 搜索函数定义
            const patterns = [
                new RegExp(`function\\s+${keyword}\\s*\\(`, 'g'),
                new RegExp(`const\\s+${keyword}\\s*=`, 'g'),
                new RegExp(`let\\s+${keyword}\\s*=`, 'g'),
                new RegExp(`var\\s+${keyword}\\s*=`, 'g'),
                new RegExp(`${keyword}\\s*:\\s*function`, 'g')
            ];

            for (let pattern of patterns) {
                let match;
                while ((match = pattern.exec(content)) !== null) {
                    const lineNum = content.substring(0, match.index).split('\n').length;
                    results.push({
                        src: src,
                        match: match[0],
                        line: lineNum,
                        context: content.substring(match.index, match.index + 200)
                    });
                }
            }
        }

        console.log(`[Debug Hook] 搜索结果 (${results.length} 个匹配):`);
        results.forEach((r, i) => {
            console.log(`\n${i + 1}. ${r.src}:${r.line}`);
            console.log(`   匹配: ${r.match}`);
            console.log(`   上下文: ${r.context.substring(0, 100)}...`);
        });

        return results;
    };

    // ========== 对象方法追踪 ==========

    /**
     * 追踪对象的所有方法调用
     * @param {object} obj - 目标对象
     * @param {string} objName - 对象名称（用于日志）
     */
    window.__trace_object__ = function(obj, objName) {
        const proto = Object.getPrototypeOf(obj);
        const methodNames = Object.getOwnPropertyNames(proto).filter(name => typeof obj[name] === 'function');

        methodNames.forEach(methodName => {
            const original = obj[methodName];
            obj[methodName] = function(...args) {
                console.log(`[Trace] ${objName}.${methodName}()`);
                console.log('参数:', args);
                return original.apply(this, args);
            };
        });

        console.log(`[Debug Hook] 正在追踪 ${objName} 的 ${methodNames.length} 个方法`);
    };

    // ========== 快捷命令 ==========

    /**
     * 自动搜索并设置断点到可能的加密函数
     */
    window.__auto_break_crypto__ = function() {
        const cryptoKeywords = ['encrypt', 'sign', 'getSign', 'makeSign', 'calcSign', 'md5', 'sha', 'hash'];

        for (let keyword of cryptoKeywords) {
            const results = window.__search_function__(keyword);
            if (results.length > 0) {
                // 尝试设置断点
                if (typeof window[keyword] === 'function') {
                    window.__set_breakpoint__(keyword);
                }
            }
        }
    };

    // ========== 导出调试日志 ==========

    window.__export_debug_logs__ = function() {
        console.log(JSON.stringify(window.__debug_config__.logs, null, 2));
        return window.__debug_config__.logs;
    };

    window.__clear_debug_logs__ = function() {
        window.__debug_config__.logs = [];
        console.log('[Debug Hook] 日志已清空');
    };

    // ========== 使用说明 ==========
    console.log(`
[Debug Hook] 可用命令:
  __set_breakpoint__(funcName)         - 设置函数断点
  __remove_breakpoint__(funcName)      - 移除断点
  __watch_var__(varName)               - 监控变量变化
  __set_conditional_breakpoint__(funcName, condition) - 设置条件断点
  __search_function__(keyword)         - 搜索函数定义
  __trace_object__(obj, name)          - 追踪对象方法
  __auto_break_crypto__()              - 自动设置加密函数断点
  __export_debug_logs__()              - 导出调试日志
  __clear_debug_logs__()               - 清空日志
    `);

    console.log('[Debug Hook] 提示: 使用 __auto_break_crypto__() 自动追踪加密函数');
})();