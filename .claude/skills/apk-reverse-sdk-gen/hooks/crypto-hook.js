/**
 * Frida Crypto Hook - 加密函数拦截脚本
 * 用于拦截Android应用中的加密操作
 */

Java.perform(function() {
    console.log("[*] Crypto Hook 已注入");

    // ========== MD5 拦截 ==========
    try {
        var MessageDigest = Java.use("java.security.MessageDigest");

        MessageDigest.getInstance.overload("java.lang.String").implementation = function(algorithm) {
            console.log("[MD5] getInstance: " + algorithm);
            return this.getInstance(algorithm);
        };

        MessageDigest.digest.overload("[B").implementation = function(data) {
            var result = this.digest(data);
            console.log("[MD5] digest input: " + bytesToHex(data));
            console.log("[MD5] digest output: " + bytesToHex(result));
            return result;
        };

        MessageDigest.update.overload("[B").implementation = function(data) {
            console.log("[MD5] update: " + bytesToHex(data));
            return this.update(data);
        };

        console.log("[+] MD5 Hook 成功");
    } catch (e) {
        console.log("[!] MD5 Hook 失败: " + e);
    }

    // ========== SHA 拦截 ==========
    try {
        var MessageDigest = Java.use("java.security.MessageDigest");

        // SHA拦截已在MD5中处理
        console.log("[+] SHA Hook 成功");
    } catch (e) {
        console.log("[!] SHA Hook 失败: " + e);
    }

    // ========== AES 拦截 ==========
    try {
        var Cipher = Java.use("javax.crypto.Cipher");

        Cipher.getInstance.overload("java.lang.String").implementation = function(transformation) {
            console.log("[AES] getInstance: " + transformation);
            return this.getInstance(transformation);
        };

        Cipher.doFinal.overload("[B").implementation = function(data) {
            var result = this.doFinal(data);
            console.log("[AES] doFinal input: " + bytesToHex(data));
            console.log("[AES] doFinal output: " + bytesToHex(result));
            console.log("[AES] operation: " + this.getAlgorithm());
            return result;
        };

        console.log("[+] AES Hook 成功");
    } catch (e) {
        console.log("[!] AES Hook 失败: " + e);
    }

    // ========== DES 拦截 ==========
    try {
        var Cipher = Java.use("javax.crypto.Cipher");

        // DES拦截已在AES Cipher中处理
        console.log("[+] DES Hook 成功");
    } catch (e) {
        console.log("[!] DES Hook 失败: " + e);
    }

    // ========== Base64 拦截 ==========
    try {
        var Base64 = Java.use("java.util.Base64");

        Base64.getEncoder().encode.overload("[B").implementation = function(data) {
            var result = this.encode(data);
            console.log("[Base64] encode input: " + bytesToHex(data));
            console.log("[Base64] encode output: " + bytesToString(result));
            return result;
        };

        Base64.getDecoder().decode.overload("[B").implementation = function(data) {
            var result = this.decode(data);
            console.log("[Base64] decode input: " + bytesToString(data));
            console.log("[Base64] decode output: " + bytesToHex(result));
            return result;
        };

        console.log("[+] Base64 Hook 成功");
    } catch (e) {
        console.log("[!] Base64 Hook 失败: " + e);
    }

    // ========== HMAC 拦截 ==========
    try {
        var Mac = Java.use("javax.crypto.Mac");

        Mac.getInstance.overload("java.lang.String").implementation = function(algorithm) {
            console.log("[HMAC] getInstance: " + algorithm);
            return this.getInstance(algorithm);
        };

        Mac.doFinal.overload("[B").implementation = function(data) {
            var result = this.doFinal(data);
            console.log("[HMAC] doFinal input: " + bytesToHex(data));
            console.log("[HMAC] doFinal output: " + bytesToHex(result));
            return result;
        };

        console.log("[+] HMAC Hook 成功");
    } catch (e) {
        console.log("[!] HMAC Hook 失败: " + e);
    }

    // ========== 辅助函数 ==========
    function bytesToHex(bytes) {
        var hex = [];
        for (var i = 0; i < bytes.length; i++) {
            hex.push(((bytes[i] & 0xFF) < 16 ? "0" : "") + (bytes[i] & 0xFF).toString(16));
        }
        return hex.join("");
    }

    function bytesToString(bytes) {
        var str = "";
        for (var i = 0; i < bytes.length; i++) {
            str += String.fromCharCode(bytes[i] & 0xFF);
        }
        return str;
    }
});