# Frida Hook注入调试指南

## 概述

Frida是一个强大的动态插桩工具，可以在运行时拦截和修改应用程序的行为。本文档介绍如何使用Frida进行APK逆向分析。

## 基础概念

### Frida架构

```
┌─────────────────┐      ┌─────────────────┐
│  Frida Client   │◄────►│  Frida Server   │
│   (PC端)        │      │  (Android设备)  │
└─────────────────┘      └─────────────────┘
        │                        │
        ▼                        ▼
   JavaScript              目标应用进程
   Hook脚本                   │
                            ▼
                       目标函数/方法
```

### 工作流程

1. 在Android设备上运行frida-server
2. PC端使用frida工具连接设备
3. 注入JavaScript Hook脚本
4. 拦截目标函数调用并记录数据

## 快速开始

### 1. 设备准备

```bash
# 检查设备连接
adb devices

# 推送frida-server
adb push frida-server /data/local/tmp/

# 启动frida-server
adb shell "su -c '/data/local/tmp/frida-server &'"

# 验证连接
frida-ps -U  # 列出设备上的进程
```

### 2. 基本Hook命令

```bash
# 附加到正在运行的应用
frida -U -n com.example.app -l hook.js

# 启动应用并注入Hook
frida -U -f com.example.app -l hook.js --no-pause

# 保存输出到文件
frida -U -f com.example.app -l hook.js -o output.log
```

## Hook脚本开发

### Java层Hook

#### 基本结构

```javascript
Java.perform(function() {
    // 在这里编写Hook代码
    console.log("[*] Hook已注入");

    // Hook目标类和方法
    var TargetClass = Java.use("com.example.TargetClass");

    TargetClass.targetMethod.implementation = function(arg1, arg2) {
        console.log("[Hook] targetMethod called");
        console.log("[Hook] arg1: " + arg1);
        console.log("[Hook] arg2: " + arg2);

        // 调用原始方法
        var result = this.targetMethod(arg1, arg2);
        console.log("[Hook] result: " + result);

        return result;
    };
});
```

#### Hook构造方法

```javascript
Java.perform(function() {
    var TargetClass = Java.use("com.example.TargetClass");

    // Hook构造方法
    TargetClass.$init.overload("java.lang.String", "int").implementation = function(str, num) {
        console.log("[Hook] Constructor called");
        console.log("[Hook] str: " + str);
        console.log("[Hook] num: " + num);

        return this.$init(str, num);
    };
});
```

#### Hook重载方法

```javascript
Java.perform(function() {
    var TargetClass = Java.use("com.example.TargetClass");

    // 指定参数类型
    TargetClass.method.overload("java.lang.String").implementation = function(arg) {
        console.log("[Hook] method(String): " + arg);
        return this.method(arg);
    };

    TargetClass.method.overload("[B").implementation = function(bytes) {
        console.log("[Hook] method(byte[]): " + bytesToHex(bytes));
        return this.method(bytes);
    };
});
```

#### Hook静态方法

```javascript
Java.perform(function() {
    var TargetClass = Java.use("com.example.TargetClass");

    TargetClass.staticMethod.implementation = function(arg) {
        console.log("[Hook] staticMethod: " + arg);
        var result = this.staticMethod(arg);
        console.log("[Hook] result: " + result);
        return result;
    };
});
```

### 加密函数Hook

#### MD5/SHA Hook

```javascript
Java.perform(function() {
    var MessageDigest = Java.use("java.security.MessageDigest");

    MessageDigest.getInstance.overload("java.lang.String").implementation = function(algorithm) {
        console.log("[MD5/SHA] getInstance: " + algorithm);
        return this.getInstance(algorithm);
    };

    MessageDigest.digest.overload("[B").implementation = function(data) {
        var result = this.digest(data);
        console.log("[MD5/SHA] Input: " + bytesToHex(data));
        console.log("[MD5/SHA] Output: " + bytesToHex(result));
        return result;
    };
});

function bytesToHex(bytes) {
    var hex = [];
    for (var i = 0; i < bytes.length; i++) {
        hex.push(((bytes[i] & 0xFF) < 16 ? "0" : "") + (bytes[i] & 0xFF).toString(16));
    }
    return hex.join("");
}
```

#### AES Hook

```javascript
Java.perform(function() {
    var Cipher = Java.use("javax.crypto.Cipher");
    var SecretKeySpec = Java.use("javax.crypto.spec.SecretKeySpec");

    // Hook密钥创建
    SecretKeySpec.$init.overload("[B", "java.lang.String").implementation = function(key, algorithm) {
        console.log("[AES] Key: " + bytesToHex(key));
        console.log("[AES] Algorithm: " + algorithm);
        return this.$init(key, algorithm);
    };

    // Hook加密/解密
    Cipher.doFinal.overload("[B").implementation = function(data) {
        var result = this.doFinal(data);
        console.log("[AES] Mode: " + this.getAlgorithm());
        console.log("[AES] Input: " + bytesToHex(data));
        console.log("[AES] Output: " + bytesToHex(result));
        return result;
    };
});
```

### HTTP请求Hook

#### OkHttp3 Hook

```javascript
Java.perform(function() {
    var OkHttpClient = Java.use("okhttp3.OkHttpClient");
    var Request = Java.use("okhttp3.Request");

    // Hook请求构建
    var RequestBuilder = Java.use("okhttp3.Request$Builder");

    RequestBuilder.url.overload("java.lang.String").implementation = function(url) {
        console.log("[OkHttp] URL: " + url);
        return this.url(url);
    };

    RequestBuilder.addHeader.implementation = function(name, value) {
        console.log("[OkHttp] Header: " + name + " = " + value);
        return this.addHeader(name, value);
    };

    RequestBuilder.post.implementation = function(body) {
        var buffer = Java.use("okio.Buffer").$new();
        body.writeTo(buffer);
        console.log("[OkHttp] POST Body: " + buffer.readUtf8());
        return this.post(body);
    };
});
```

### Native层Hook

```javascript
// Hook Native函数
Interceptor.attach(Module.findExportByName("libnative.so", "Java_com_example_Native_method"), {
    onEnter: function(args) {
        console.log("[Native] method called");
        console.log("[Native] args[0]: " + args[0]);
        console.log("[Native] args[1]: " + args[1]);

        // 读取字符串参数
        var str = Memory.readUtf8String(args[2]);
        console.log("[Native] arg string: " + str);
    },
    onLeave: function(retval) {
        console.log("[Native] return: " + retval);
    }
});
```

## 使用本Skill提供的Hook脚本

### 可用Hook脚本

| 脚本 | 用途 |
|------|------|
| `crypto-hook.js` | 加密函数拦截 |
| `api-hook.js` | HTTP请求拦截 |
| `native-hook.js` | Native函数拦截 |
| `string-hook.js` | 字符串操作追踪 |
| `all-in-one-hook.js` | 综合Hook（推荐） |

### 使用方法

```bash
# 进入项目目录
cd apk-projects/com.example.app

# 使用综合Hook
frida -U -f com.example.app -l hooks/all-in-one-hook.js --no-pause -o hook-output/output.log

# 仅Hook加密函数
frida -U -f com.example.app -l hooks/crypto-hook.js --no-pause

# Hook HTTP请求
frida -U -f com.example.app -l hooks/api-hook.js --no-pause
```

## 调试技巧

### 1. 打印调用栈

```javascript
Java.perform(function() {
    var TargetClass = Java.use("com.example.TargetClass");

    TargetClass.method.implementation = function(arg) {
        console.log("[Hook] method called from:");
        console.log(Java.use("android.util.Log").getStackTraceString(Java.use("java.lang.Exception").$new()));
        return this.method(arg);
    };
});
```

### 2. 动态查找类

```javascript
Java.perform(function() {
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.indexOf("sign") !== -1 || className.indexOf("encrypt") !== -1) {
                console.log("[*] Found class: " + className);
            }
        },
        onComplete: function() {
            console.log("[*] Class enumeration complete");
        }
    });
});
```

### 3. 修改返回值

```javascript
Java.perform(function() {
    var TargetClass = Java.use("com.example.TargetClass");

    TargetClass.checkSign.implementation = function() {
        console.log("[Hook] checkSign bypassed");
        return true;  // 强制返回true
    };
});
```

## 常见问题

### 1. 注入失败

- 确保frida-server与frida版本匹配
- 检查设备是否root
- 检查SELinux设置

### 2. 找不到类

- 确保类已加载（可能需要延迟注入）
- 检查类名是否被混淆

### 3. Hook不生效

- 检查方法签名是否正确
- 使用`overload()`指定参数类型
- 检查是否被其他Hook覆盖