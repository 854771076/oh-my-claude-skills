/**
 * Fetch Hook - 拦截所有Fetch请求
 * 用于记录请求参数、响应数据、调用栈
 *
 * 使用方式：
 * 1. 在浏览器控制台直接粘贴执行
 * 2. 或通过Playwright的page.evaluate()注入
 */

(function() {
    console.log('[Fetch Hook] 开始拦截Fetch请求...');

    // 存储拦截数据
    window.__fetch_intercept_data__ = [];

    // 保存原始fetch
    const originalFetch = window.fetch;

    // 重写fetch
    window.fetch = function(input, init = {}) {
        const startTime = Date.now();

        // 解析请求信息
        let url, method, body, headers;

        if (typeof input === 'string') {
            url = input;
        } else if (input instanceof Request) {
            url = input.url;
            method = input.method;
            headers = {};
            input.headers.forEach((v, k) => headers[k] = v);
        } else if (input instanceof URL) {
            url = input.toString();
        }

        method = method || init.method || 'GET';
        body = init.body;
        headers = headers || init.headers || {};

        const requestData = {
            url: url,
            method: method,
            headers: headers,
            body: body,
            startTime: startTime
        };

        console.log(`[Fetch Hook] ${method} ${url}`);
        if (body) {
            console.log('[Fetch Hook] 请求体:', typeof body === 'string' ? body.substring(0, 500) : body);
        }

        // 获取调用栈
        try {
            throw new Error('Stack trace');
        } catch (e) {
            requestData.callStack = e.stack;
            console.log('[Fetch Hook] 调用栈:', e.stack.split('\n').slice(0, 5).join('\n'));
        }

        // 调用原始fetch
        return originalFetch.apply(this, arguments).then(response => {
            const endTime = Date.now();
            requestData.duration = endTime - startTime;
            requestData.status = response.status;
            requestData.ok = response.ok;

            console.log(`[Fetch Hook] 响应: ${response.status} (${requestData.duration}ms)`);

            // 克隆响应以读取内容
            const clonedResponse = response.clone();
            clonedResponse.text().then(text => {
                requestData.responseBody = text.substring(0, 5000);
                console.log('[Fetch Hook] 响应数据:', text.substring(0, 500));

                // 保存数据
                window.__fetch_intercept_data__.push(requestData);
            }).catch(() => {
                // 可能是二进制数据
                requestData.responseBody = '[Binary data]';
                window.__fetch_intercept_data__.push(requestData);
            });

            return response;
        }).catch(error => {
            requestData.error = error.message;
            console.error('[Fetch Hook] 请求失败:', error);
            window.__fetch_intercept_data__.push(requestData);
            throw error;
        });
    };

    // 添加数据导出函数
    window.__export_fetch_data__ = function() {
        console.log(JSON.stringify(window.__fetch_intercept_data__, null, 2));
        return window.__fetch_intercept_data__;
    };

    // 添加数据清空函数
    window.__clear_fetch_data__ = function() {
        window.__fetch_intercept_data__ = [];
        console.log('[Fetch Hook] 数据已清空');
    };

    console.log('[Fetch Hook] 拦截已启用');
    console.log('[Fetch Hook] 使用 __export_fetch_data__() 导出数据');
})();