/**
 * Frida API Hook - HTTP请求拦截脚本
 * 用于拦截Android应用中的HTTP/HTTPS请求
 */

Java.perform(function() {
    console.log("[*] API Hook 已注入");

    // ========== OkHttp3 拦截 ==========
    try {
        var OkHttpClient = Java.use("okhttp3.OkHttpClient");
        var Request = Java.use("okhttp3.Request");
        var RequestBody = Java.use("okhttp3.RequestBody");
        var Response = Java.use("okhttp3.Response");

        var Interceptor = Java.use("okhttp3.Interceptor");
        var Chain = Java.use("okhttp3.Interceptor.Chain");

        // 创建自定义拦截器
        var MyInterceptor = Java.registerClass({
            name: "com.frida.MyInterceptor",
            implements: [Interceptor],
            methods: {
                intercept: function(chain) {
                    var request = chain.request();
                    var url = request.url().toString();
                    var method = request.method();
                    var headers = request.headers();

                    console.log("[OkHttp] URL: " + url);
                    console.log("[OkHttp] Method: " + method);
                    console.log("[OkHttp] Headers: " + headers.toString());

                    // 打印请求体
                    try {
                        var body = request.body();
                        if (body) {
                            var buffer = Java.use("okio.Buffer").$new();
                            body.writeTo(buffer);
                            console.log("[OkHttp] Body: " + buffer.readUtf8());
                        }
                    } catch (e) {
                        console.log("[OkHttp] Body: 无法读取");
                    }

                    var response = chain.proceed(request);

                    // 打印响应
                    console.log("[OkHttp] Response Code: " + response.code());
                    try {
                        var responseBody = response.body();
                        if (responseBody) {
                            var source = responseBody.source();
                            source.request(Java.use("java.lang.Long").MAX_VALUE.value);
                            var buffer = source.buffer();
                            console.log("[OkHttp] Response Body: " + buffer.clone().readUtf8());
                        }
                    } catch (e) {}

                    return response;
                }
            }
        });

        // 注入拦截器
        OkHttpClient.newBuilder.implementation = function() {
            var builder = this.newBuilder();
            builder.addInterceptor(MyInterceptor.$new());
            return builder;
        };

        console.log("[+] OkHttp3 Hook 成功");
    } catch (e) {
        console.log("[!] OkHttp3 Hook 失败: " + e);
    }

    // ========== HttpURLConnection 拦截 ==========
    try {
        var HttpURLConnection = Java.use("java.net.HttpURLConnection");

        HttpURLConnection.getInputStream.implementation = function() {
            console.log("[HttpURLConnection] URL: " + this.getURL().toString());
            console.log("[HttpURLConnection] Method: " + this.getRequestMethod());
            console.log("[HttpURLConnection] Response Code: " + this.getResponseCode());

            // 打印请求头
            var headers = this.getRequestProperties();
            console.log("[HttpURLConnection] Headers: " + headers.toString());

            return this.getInputStream();
        };

        HttpURLConnection.getOutputStream.implementation = function() {
            console.log("[HttpURLConnection] URL: " + this.getURL().toString());
            console.log("[HttpURLConnection] Method: " + this.getRequestMethod());

            return this.getOutputStream();
        };

        console.log("[+] HttpURLConnection Hook 成功");
    } catch (e) {
        console.log("[!] HttpURLConnection Hook 失败: " + e);
    }

    // ========== Retrofit 拦截 ==========
    try {
        var ServiceMethod = Java.use("retrofit2.ServiceMethod");

        ServiceMethod.invoke.implementation = function(args) {
            console.log("[Retrofit] Method: " + this.method);
            console.log("[Retrofit] Path: " + this.relativePath);
            console.log("[Retrofit] Args: " + JSON.stringify(args));

            return this.invoke(args);
        };

        console.log("[+] Retrofit Hook 成功");
    } catch (e) {
        console.log("[!] Retrofit Hook 失败: " + e);
    }

    // ========== Volley 拦截 ==========
    try {
        var Request = Java.use("com.android.volley.Request");

        Request.getUrl.implementation = function() {
            var url = this.getUrl();
            console.log("[Volley] URL: " + url);
            console.log("[Volley] Method: " + this.getMethod());
            console.log("[Volley] Headers: " + this.getHeaders());

            return url;
        };

        console.log("[+] Volley Hook 成功");
    } catch (e) {
        console.log("[!] Volley Hook 失败: " + e);
    }
});