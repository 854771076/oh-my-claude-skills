/**
 * Frida All-in-One Hook - 综合Hook脚本
 * 包含加密、API、Native、字符串等所有Hook功能
 */

Java.perform(function() {
    console.log("========================================");
    console.log("[*] All-in-One Hook 已注入");
    console.log("========================================");

    // ========== 辅助函数 ==========
    function bytesToHex(bytes, maxLen) {
        maxLen = maxLen || 256;
        var hex = [];
        for (var i = 0; i < bytes.length && i < maxLen; i++) {
            hex.push(((bytes[i] & 0xFF) < 16 ? "0" : "") + (bytes[i] & 0xFF).toString(16));
        }
        if (bytes.length > maxLen) hex.push("...");
        return hex.join("");
    }

    function bytesToString(bytes, maxLen) {
        maxLen = maxLen || 256;
        var str = "";
        for (var i = 0; i < bytes.length && i < maxLen; i++) {
            var c = bytes[i] & 0xFF;
            if (c >= 32 && c <= 126) {
                str += String.fromCharCode(c);
            } else {
                str += ".";
            }
        }
        return str;
    }

    function logCall(tag, method, info) {
        console.log("\n[" + tag + "] ========== " + method + " ========== ");
        console.log(info);
    }

    // ========== 加密函数 Hook ==========

    // MessageDigest (MD5/SHA)
    try {
        var MessageDigest = Java.use("java.security.MessageDigest");

        MessageDigest.getInstance.overload("java.lang.String").implementation = function(algorithm) {
            logCall("CRYPTO", "MessageDigest.getInstance", "Algorithm: " + algorithm);
            return this.getInstance(algorithm);
        };

        MessageDigest.digest.overload("[B").implementation = function(data) {
            var result = this.digest(data);
            var algo = this.getAlgorithm();
            logCall("CRYPTO", "MessageDigest.digest",
                "Algorithm: " + algo + "\n" +
                "Input: " + bytesToHex(data) + "\n" +
                "Output: " + bytesToHex(result));
            return result;
        };

        console.log("[+] MessageDigest Hook 成功");
    } catch (e) {
        console.log("[!] MessageDigest Hook 失败: " + e);
    }

    // Cipher (AES/DES)
    try {
        var Cipher = Java.use("javax.crypto.Cipher");

        Cipher.getInstance.overload("java.lang.String").implementation = function(transformation) {
            logCall("CRYPTO", "Cipher.getInstance", "Transformation: " + transformation);
            return this.getInstance(transformation);
        };

        Cipher.doFinal.overload("[B").implementation = function(data) {
            var result = this.doFinal(data);
            var op = this.getAlgorithm();
            logCall("CRYPTO", "Cipher.doFinal",
                "Algorithm: " + op + "\n" +
                "Input (" + data.length + " bytes): " + bytesToHex(data) + "\n" +
                "Output (" + result.length + " bytes): " + bytesToHex(result));
            return result;
        };

        console.log("[+] Cipher Hook 成功");
    } catch (e) {
        console.log("[!] Cipher Hook 失败: " + e);
    }

    // Base64
    try {
        var Base64 = Java.use("java.util.Base64");
        var Encoder = Java.use("java.util.Base64$Encoder");
        var Decoder = Java.use("java.util.Base64$Decoder");

        Base64.getEncoder().encode.overload("[B").implementation = function(data) {
            var result = this.encode(data);
            logCall("CRYPTO", "Base64.encode",
                "Input: " + bytesToHex(data) + "\n" +
                "Output: " + bytesToString(result));
            return result;
        };

        Base64.getDecoder().decode.overload("[B").implementation = function(data) {
            var result = this.decode(data);
            logCall("CRYPTO", "Base64.decode",
                "Input: " + bytesToString(data) + "\n" +
                "Output: " + bytesToHex(result));
            return result;
        };

        console.log("[+] Base64 Hook 成功");
    } catch (e) {
        console.log("[!] Base64 Hook 失败: " + e);
    }

    // Mac (HMAC)
    try {
        var Mac = Java.use("javax.crypto.Mac");

        Mac.doFinal.overload("[B").implementation = function(data) {
            var result = this.doFinal(data);
            logCall("CRYPTO", "Mac.doFinal",
                "Algorithm: " + this.getAlgorithm() + "\n" +
                "Input: " + bytesToHex(data) + "\n" +
                "Output: " + bytesToHex(result));
            return result;
        };

        console.log("[+] Mac Hook 成功");
    } catch (e) {
        console.log("[!] Mac Hook 失败: " + e);
    }

    // ========== HTTP请求 Hook ==========

    // OkHttp3
    try {
        var RequestBuilder = Java.use("okhttp3.Request$Builder");

        RequestBuilder.url.overload("java.lang.String").implementation = function(url) {
            logCall("HTTP", "RequestBuilder.url", "URL: " + url);
            return this.url(url);
        };

        RequestBuilder.addHeader.implementation = function(name, value) {
            logCall("HTTP", "RequestBuilder.addHeader", name + ": " + value);
            return this.addHeader(name, value);
        };

        RequestBuilder.post.implementation = function(body) {
            try {
                var buffer = Java.use("okio.Buffer").$new();
                body.writeTo(buffer);
                logCall("HTTP", "RequestBuilder.post", "Body: " + buffer.readUtf8());
            } catch (e) {}
            return this.post(body);
        };

        console.log("[+] OkHttp3 Hook 成功");
    } catch (e) {
        console.log("[!] OkHttp3 Hook 失败: " + e);
    }

    // HttpURLConnection
    try {
        var HttpURLConnection = Java.use("java.net.HttpURLConnection");

        HttpURLConnection.setRequestProperty.implementation = function(key, value) {
            logCall("HTTP", "HttpURLConnection.setHeader", key + ": " + value);
            return this.setRequestProperty(key, value);
        };

        HttpURLConnection.getOutputStream.implementation = function() {
            console.log("[HTTP] HttpURLConnection.getOutputStream - URL: " + this.getURL());
            return this.getOutputStream();
        };

        console.log("[+] HttpURLConnection Hook 成功");
    } catch (e) {
        console.log("[!] HttpURLConnection Hook 失败: " + e);
    }

    // ========== 字符串操作 Hook ==========

    try {
        var StringBuilder = Java.use("java.lang.StringBuilder");

        StringBuilder.toString.implementation = function() {
            var result = this.toString();
            // 只打印较长的字符串（可能包含签名）
            if (result.length > 16 && result.length < 128) {
                logCall("STRING", "StringBuilder.toString", result);
            }
            return result;
        };

        console.log("[+] StringBuilder Hook 成功");
    } catch (e) {
        console.log("[!] StringBuilder Hook 失败: " + e);
    }

    // ========== 签名参数搜索 ==========

    try {
        // 搜索常见签名参数名
        var signParams = ["sign", "signature", "token", "md5", "sig", "checksum", "auth"];

        var String = Java.use("java.lang.String");

        String.contains.implementation = function(str) {
            var result = this.contains(str);
            for (var i = 0; i < signParams.length; i++) {
                if (str.toLowerCase() === signParams[i] || this.toLowerCase().contains(signParams[i])) {
                    logCall("SIGN", "String.contains",
                        "Checking: '" + this + "' contains '" + str + "' -> " + result);
                    break;
                }
            }
            return result;
        };

        console.log("[+] Sign Search Hook 成功");
    } catch (e) {
        console.log("[!] Sign Search Hook 失败: " + e);
    }

    console.log("========================================");
    console.log("[*] All-in-One Hook 加载完成");
    console.log("========================================");
});