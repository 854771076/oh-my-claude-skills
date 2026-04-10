/**
 * Frida Native Hook - Native函数调用拦截脚本
 * 用于拦截Android应用中的Native层加密操作
 */

Interceptor.attach(Module.findExportByName(null, "Java_com_*"), {
    onEnter: function(args) {
        console.log("[Native] JNI call detected");
        console.log("[Native] Args[0]: " + args[0]);
        console.log("[Native] Args[1]: " + args[1]);
    },
    onLeave: function(retval) {
        console.log("[Native] Return: " + retval);
    }
});

// ========== MD5 Native Hook ==========
try {
    var md5_module = Module.findExportByName(null, "MD5");
    if (md5_module) {
        Interceptor.attach(md5_module, {
            onEnter: function(args) {
                console.log("[NativeMD5] Input addr: " + args[0]);
                var input = Memory.readByteArray(args[0], args[1]);
                console.log("[NativeMD5] Input length: " + args[1]);
                console.log("[NativeMD5] Input: " + hexdump(input));
            },
            onLeave: function(retval) {
                if (retval) {
                    var output = Memory.readByteArray(retval, 16);
                    console.log("[NativeMD5] Output: " + hexdump(output));
                }
            }
        });
        console.log("[+] Native MD5 Hook 成功");
    }
} catch (e) {
    console.log("[!] Native MD5 Hook 失败: " + e);
}

// ========== AES Native Hook ==========
try {
    // 尝试常见AES函数名
    var aes_funcs = ["AES_encrypt", "AES_decrypt", "aes_encrypt", "aes_decrypt"];
    for (var i = 0; i < aes_funcs.length; i++) {
        var func = Module.findExportByName(null, aes_funcs[i]);
        if (func) {
            Interceptor.attach(func, {
                onEnter: function(args) {
                    console.log("[NativeAES] Function called");
                    console.log("[NativeAES] Input addr: " + args[0]);
                    console.log("[NativeAES] Key addr: " + args[1]);
                },
                onLeave: function(retval) {
                    console.log("[NativeAES] Output addr: " + retval);
                }
            });
            console.log("[+] Native AES Hook 成功: " + aes_funcs[i]);
        }
    }
} catch (e) {
    console.log("[!] Native AES Hook 失败: " + e);
}

// ========== Base64 Native Hook ==========
try {
    var b64_funcs = ["base64_encode", "base64_decode", "B64_encode", "B64_decode"];
    for (var i = 0; i < b64_funcs.length; i++) {
        var func = Module.findExportByName(null, b64_funcs[i]);
        if (func) {
            Interceptor.attach(func, {
                onEnter: function(args) {
                    console.log("[NativeB64] Function called");
                    var input = Memory.readByteArray(args[0], args[1]);
                    console.log("[NativeB64] Input: " + hexdump(input, { length: args[1] }));
                },
                onLeave: function(retval) {
                    console.log("[NativeB64] Output: " + Memory.readUtf8String(retval));
                }
            });
            console.log("[+] Native Base64 Hook 成功: " + b64_funcs[i]);
        }
    }
} catch (e) {
    console.log("[!] Native Base64 Hook 失败: " + e);
}

// ========== 字符串操作 Hook ==========
try {
    var strlen = Module.findExportByName(null, "strlen");
    if (strlen) {
        Interceptor.attach(strlen, {
            onEnter: function(args) {
                var str = Memory.readUtf8String(args[0]);
                if (str && str.length > 5 && str.length < 100) {
                    console.log("[strlen] String: " + str);
                }
            },
            onLeave: function(retval) {
                // 长度值
            }
        });
    }

    var strcmp = Module.findExportByName(null, "strcmp");
    if (strcmp) {
        Interceptor.attach(strcmp, {
            onEnter: function(args) {
                var str1 = Memory.readUtf8String(args[0]);
                var str2 = Memory.readUtf8String(args[1]);
                if (str1 && str2) {
                    console.log("[strcmp] String1: " + str1);
                    console.log("[strcmp] String2: " + str2);
                }
            },
            onLeave: function(retval) {
                console.log("[strcmp] Result: " + retval);
            }
        });
    }

    console.log("[+] Native String Hook 成功");
} catch (e) {
    console.log("[!] Native String Hook 失败: " + e);
}

// ========== 辅助函数 ==========
function hexdump(buffer, options) {
    options = options || {};
    var length = options.length || buffer.length;
    var result = "";
    for (var i = 0; i < length; i++) {
        var byte = buffer[i];
        result += ((byte & 0xFF) < 16 ? "0" : "") + (byte & 0xFF).toString(16) + " ";
        if ((i + 1) % 16 === 0) {
            result += "\n";
        }
    }
    return result;
}

console.log("[*] Native Hook 脚本加载完成");