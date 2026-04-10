/**
 * Frida String Hook - 字符串操作追踪脚本
 * 用于追踪Android应用中的字符串创建和操作
 */

Java.perform(function() {
    console.log("[*] String Hook 已注入");

    // ========== String 创建 Hook ==========
    try {
        var String = Java.use("java.lang.String");

        // 拦截各种String构造方法
        String.$init.overload("[B").implementation = function(bytes) {
            console.log("[String] new String(byte[]): " + bytesToHex(bytes));
            return this.$init(bytes);
        };

        String.$init.overload("[B", "int", "int").implementation = function(bytes, offset, len) {
            var subarray = Java.array("byte", bytes.slice(offset, offset + len));
            console.log("[String] new String(byte[], offset, len): " + bytesToHex(subarray));
            return this.$init(bytes, offset, len);
        };

        String.$init.overload("java.lang.String").implementation = function(original) {
            console.log("[String] new String(String): " + original);
            return this.$init(original);
        };

        console.log("[+] String Creation Hook 成功");
    } catch (e) {
        console.log("[!] String Creation Hook 失败: " + e);
    }

    // ========== StringBuilder Hook ==========
    try {
        var StringBuilder = Java.use("java.lang.StringBuilder");

        StringBuilder.append.overload("java.lang.String").implementation = function(str) {
            console.log("[StringBuilder] append(String): " + str);
            console.log("[StringBuilder] current: " + this.toString());
            return this.append(str);
        };

        StringBuilder.toString.implementation = function() {
            var result = this.toString();
            console.log("[StringBuilder] toString(): " + result);
            return result;
        };

        console.log("[+] StringBuilder Hook 成功");
    } catch (e) {
        console.log("[!] StringBuilder Hook 失败: " + e);
    }

    // ========== StringBuffer Hook ==========
    try {
        var StringBuffer = Java.use("java.lang.StringBuffer");

        StringBuffer.append.overload("java.lang.String").implementation = function(str) {
            console.log("[StringBuffer] append(String): " + str);
            return this.append(str);
        };

        StringBuffer.toString.implementation = function() {
            var result = this.toString();
            console.log("[StringBuffer] toString(): " + result);
            return result;
        };

        console.log("[+] StringBuffer Hook 成功");
    } catch (e) {
        console.log("[!] StringBuffer Hook 失败: " + e);
    }

    // ========== String 拼接操作 Hook ==========
    try {
        var String = Java.use("java.lang.String");

        String.concat.implementation = function(str) {
            var result = this.concat(str);
            console.log("[String] concat: this=" + this + ", arg=" + str + ", result=" + result);
            return result;
        };

        String.replace.overload("java.lang.String", "java.lang.String").implementation = function(oldStr, newStr) {
            var result = this.replace(oldStr, newStr);
            console.log("[String] replace: " + this + " -> " + result);
            return result;
        };

        String.substring.overload("int").implementation = function(start) {
            var result = this.substring(start);
            console.log("[String] substring(start): " + this + " -> " + result);
            return result;
        };

        String.substring.overload("int", "int").implementation = function(start, end) {
            var result = this.substring(start, end);
            console.log("[String] substring(start, end): " + this + " -> " + result);
            return result;
        };

        console.log("[+] String Operations Hook 成功");
    } catch (e) {
        console.log("[!] String Operations Hook 失败: " + e);
    }

    // ========== 字节数组转字符串 Hook ==========
    try {
        // 常见编码类
        var Charset = Java.use("java.nio.charset.Charset");

        String.$init.overload("[B", "java.nio.charset.Charset").implementation = function(bytes, charset) {
            console.log("[String] new String(bytes, charset): charset=" + charset.name());
            console.log("[String] bytes: " + bytesToHex(bytes));
            return this.$init(bytes, charset);
        };

        console.log("[+] Charset Hook 成功");
    } catch (e) {
        console.log("[!] Charset Hook 失败: " + e);
    }

    // ========== 辅助函数 ==========
    function bytesToHex(bytes) {
        var hex = [];
        for (var i = 0; i < bytes.length && i < 256; i++) {
            hex.push(((bytes[i] & 0xFF) < 16 ? "0" : "") + (bytes[i] & 0xFF).toString(16));
        }
        return hex.join("");
    }
});