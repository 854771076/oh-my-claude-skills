/**
 * Crypto Hook - 拦截常见加密函数调用
 * 用于逆向分析时定位加密函数和参数
 *
 * 支持拦截：
 * - CryptoJS (MD5, SHA1, SHA256, AES, DES, etc.)
 * - 原生Web Crypto API
 * - Base64编码/解码
 * - 自定义加密函数
 */

(function() {
    console.log('[Crypto Hook] 开始拦截加密函数...');

    // 存储拦截数据
    window.__crypto_intercept_data__ = [];

    // ========== 拦截 CryptoJS ==========

    if (window.CryptoJS) {
        console.log('[Crypto Hook] 检测到 CryptoJS');

        // MD5
        if (CryptoJS.MD5) {
            const originalMD5 = CryptoJS.MD5;
            CryptoJS.MD5 = function(message) {
                const input = message.toString();
                const result = originalMD5.apply(this, arguments);
                const output = result.toString();

                const record = {
                    type: 'CryptoJS.MD5',
                    input: input.substring(0, 500),
                    output: output,
                    timestamp: Date.now()
                };

                window.__crypto_intercept_data__.push(record);
                console.log('[Crypto Hook] MD5 输入:', input.substring(0, 200));
                console.log('[Crypto Hook] MD5 输出:', output);
                console.trace('[Crypto Hook] 调用栈');

                return result;
            };
        }

        // SHA1
        if (CryptoJS.SHA1) {
            const originalSHA1 = CryptoJS.SHA1;
            CryptoJS.SHA1 = function(message) {
                const input = message.toString();
                const result = originalSHA1.apply(this, arguments);
                const output = result.toString();

                window.__crypto_intercept_data__.push({
                    type: 'CryptoJS.SHA1',
                    input: input.substring(0, 500),
                    output: output,
                    timestamp: Date.now()
                });

                console.log('[Crypto Hook] SHA1:', input.substring(0, 100), '->', output);
                console.trace('[Crypto Hook] 调用栈');

                return result;
            };
        }

        // SHA256
        if (CryptoJS.SHA256) {
            const originalSHA256 = CryptoJS.SHA256;
            CryptoJS.SHA256 = function(message) {
                const input = message.toString();
                const result = originalSHA256.apply(this, arguments);
                const output = result.toString();

                window.__crypto_intercept_data__.push({
                    type: 'CryptoJS.SHA256',
                    input: input.substring(0, 500),
                    output: output,
                    timestamp: Date.now()
                });

                console.log('[Crypto Hook] SHA256:', input.substring(0, 100), '->', output);
                console.trace('[Crypto Hook] 调用栈');

                return result;
            };
        }

        // AES加密
        if (CryptoJS.AES && CryptoJS.AES.encrypt) {
            const originalAESEncrypt = CryptoJS.AES.encrypt;
            CryptoJS.AES.encrypt = function(message, key, cfg) {
                const result = originalAESEncrypt.apply(this, arguments);

                window.__crypto_intercept_data__.push({
                    type: 'CryptoJS.AES.encrypt',
                    message: message.toString().substring(0, 200),
                    key: key.toString(),
                    result: result.toString(),
                    timestamp: Date.now()
                });

                console.log('[Crypto Hook] AES加密:');
                console.log('  消息:', message.toString().substring(0, 100));
                console.log('  密钥:', key.toString());
                console.log('  结果:', result.toString());
                console.trace('[Crypto Hook] 调用栈');

                return result;
            };
        }

        // AES解密
        if (CryptoJS.AES && CryptoJS.AES.decrypt) {
            const originalAESDecrypt = CryptoJS.AES.decrypt;
            CryptoJS.AES.decrypt = function(ciphertext, key, cfg) {
                const result = originalAESDecrypt.apply(this, arguments);

                window.__crypto_intercept_data__.push({
                    type: 'CryptoJS.AES.decrypt',
                    ciphertext: ciphertext.toString(),
                    key: key.toString(),
                    timestamp: Date.now()
                });

                console.log('[Crypto Hook] AES解密:', ciphertext.toString().substring(0, 100));
                console.trace('[Crypto Hook] 调用栈');

                return result;
            };
        }

        // HmacSHA256
        if (CryptoJS.HmacSHA256) {
            const originalHmacSHA256 = CryptoJS.HmacSHA256;
            CryptoJS.HmacSHA256 = function(message, key) {
                const result = originalHmacSHA256.apply(this, arguments);

                window.__crypto_intercept_data__.push({
                    type: 'CryptoJS.HmacSHA256',
                    message: message.toString().substring(0, 200),
                    key: key.toString(),
                    output: result.toString(),
                    timestamp: Date.now()
                });

                console.log('[Crypto Hook] HmacSHA256:', message.toString().substring(0, 100), '+', key.toString(), '->', result.toString());
                console.trace('[Crypto Hook] 调用栈');

                return result;
            };
        }
    }

    // ========== 拦截 Base64 ==========

    // btoa (编码)
    const originalBtoa = window.btoa;
    window.btoa = function(str) {
        const result = originalBtoa.apply(this, arguments);

        window.__crypto_intercept_data__.push({
            type: 'btoa',
            input: str.substring(0, 500),
            output: result,
            timestamp: Date.now()
        });

        console.log('[Crypto Hook] Base64编码:', str.substring(0, 100), '->', result.substring(0, 100));
        console.trace('[Crypto Hook] 调用栈');

        return result;
    };

    // atob (解码)
    const originalAtob = window.atob;
    window.atob = function(str) {
        const result = originalAtob.apply(this, arguments);

        window.__crypto_intercept_data__.push({
            type: 'atob',
            input: str.substring(0, 500),
            output: result,
            timestamp: Date.now()
        });

        console.log('[Crypto Hook] Base64解码:', str.substring(0, 100), '->', result.substring(0, 100));
        console.trace('[Crypto Hook] 调用栈');

        return result;
    };

    // ========== 拦截 encodeURIComponent (常用于签名前的参数编码) ==========

    const originalEncodeURIComponent = window.encodeURIComponent;
    window.encodeURIComponent = function(str) {
        const result = originalEncodeURIComponent.apply(this, arguments);

        // 只记录较长的编码操作（通常是签名参数）
        if (str.length > 20) {
            window.__crypto_intercept_data__.push({
                type: 'encodeURIComponent',
                input: str.substring(0, 200),
                output: result.substring(0, 200),
                timestamp: Date.now()
            });

            console.log('[Crypto Hook] URL编码:', str.substring(0, 100));
            console.trace('[Crypto Hook] 调用栈');
        }

        return result;
    };

    // ========== 数据导出函数 ==========

    window.__export_crypto_data__ = function() {
        console.log(JSON.stringify(window.__crypto_intercept_data__, null, 2));
        return window.__crypto_intercept_data__;
    };

    window.__clear_crypto_data__ = function() {
        window.__crypto_intercept_data__ = [];
        console.log('[Crypto Hook] 数据已清空');
    };

    // ========== 搜索加密函数 ==========

    window.__find_crypto_functions__ = function() {
        const scripts = document.getElementsByTagName('script');
        const results = [];

        for (let script of scripts) {
            const content = script.textContent || '';
            const src = script.src || 'inline';

            const keywords = ['md5', 'sha', 'encrypt', 'sign', 'crypto', 'hash', 'base64', 'btoa', 'atob'];
            const found = keywords.filter(kw => content.toLowerCase().includes(kw));

            if (found.length > 0) {
                results.push({
                    src: src,
                    keywords: found,
                    length: content.length
                });
            }
        }

        console.log('[Crypto Hook] 找到包含加密关键词的脚本:');
        console.table(results);
        return results;
    };

    console.log('[Crypto Hook] 拦截已启用');
    console.log('[Crypto Hook] 使用 __export_crypto_data__() 导出数据');
    console.log('[Crypto Hook] 使用 __find_crypto_functions__() 搜索加密函数');
})();