#!/usr/bin/env python3
"""
动态API SDK模板（无加密参数）
用于生成调用RESTful API的SDK代码

支持生成：
- Python SDK（requests/aiohttp）
- JavaScript SDK（axios/fetch）
- Java SDK（OkHttp）
"""

import datetime

# ==================== Python SDK模板 ====================

PYTHON_SDK_TEMPLATE = '''
#!/usr/bin/env python3
"""
{title} - API调用SDK

API URL: {api_url}
生成时间: {generated_time}
请求方法: {method}
认证方式: {auth_type}

使用示例:
    from {module_name} import {client_class}

    client = {client_class}()
    result = client.{main_method}({params_example})
    print(result)
"""

import requests
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {client_class}:
    """API客户端"""

    def __init__(self, base_url: str = "{base_url}", timeout: int = 30):
        """
        初始化客户端

        Args:
            base_url: API基础URL
            timeout: 请求超时时间
        """
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        """设置请求头"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': '{title}-SDK/1.0'
        })
        {auth_setup}

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_times: int = 3
    ) -> Dict:
        """
        发送请求（带重试）

        Args:
            method: HTTP方法
            endpoint: API端点
            params: 查询参数
            data: POST数据
            retry_times: 重试次数

        Returns:
            响应数据
        """
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(retry_times):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}): {e}")
                if attempt < retry_times - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    {methods}

    # 异步版本（使用aiohttp）
    async def _async_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """异步请求"""
        url = f"{self.base_url}/{endpoint}"

        async with aiohttp.ClientSession(headers=self.session.headers) as session:
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                return await response.json()

    def close(self):
        """关闭会话"""
        self.session.close()


if __name__ == '__main__':
    client = {client_class}()
    try:
        result = client.{main_method}({params_example})
        print(f"响应: {result}")
    finally:
        client.close()
'''

# ==================== JavaScript SDK模板 ====================

JS_SDK_TEMPLATE = '''
/**
 * {title} - API调用SDK
 *
 * API URL: {api_url}
 * 生成时间: {generated_time}
 * 请求方法: {method}
 *
 * 使用示例:
 *   const client = new {client_class}();
 *   const result = await client.{main_method}({params_example});
 *   console.log(result);
 */

class {client_class} {
    /**
     * 初始化客户端
     * @param {string} baseUrl - API基础URL
     * @param {number} timeout - 超时时间（毫秒）
     */
    constructor(baseUrl = '{base_url}', timeout = 30000) {
        this.baseUrl = baseUrl;
        this.timeout = timeout;
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': '{title}-SDK/1.0'
        };
        {auth_setup}
    }

    /**
     * 发送请求
     * @param {string} method - HTTP方法
     * @param {string} endpoint - API端点
     * @param {object} params - 查询参数
     * @param {object} data - POST数据
     * @returns {Promise<object>} 响应数据
     */
    async request(method, endpoint, params = null, data = null) {
        const url = new URL(`${this.baseUrl}/${endpoint}`);
        if (params) {
            Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
        }

        const options = {
            method: method,
            headers: this.headers,
            timeout: this.timeout
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url.toString(), options);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    {methods}
}

// 使用示例
if (typeof module !== 'undefined') {
    module.exports = {client_class};
}
'''

# ==================== Java SDK模板 ====================

JAVA_SDK_TEMPLATE = '''
import okhttp3.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.TimeUnit;
import java.io.IOException;

/**
 * {title} - API调用SDK
 *
 * API URL: {api_url}
 * 生成时间: {generated_time}
 */
public class {client_class} {

    private final String baseUrl;
    private final OkHttpClient client;
    private final ObjectMapper objectMapper;
    {auth_field}

    /**
     * 初始化客户端
     * @param baseUrl API基础URL
     */
    public {client_class}(String baseUrl) {
        this.baseUrl = baseUrl;
        this.client = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();
        this.objectMapper = new ObjectMapper();
        {auth_init}
    }

    public {client_class}() {
        this("{base_url}");
    }

    /**
     * 发送请求
     */
    private Map<String, Object> request(String method, String endpoint,
                                         Map<String, Object> params,
                                         Map<String, Object> data) throws IOException {
        HttpUrl.Builder urlBuilder = HttpUrl.parse(baseUrl + "/" + endpoint).newBuilder();
        if (params != null) {
            for (Map.Entry<String, Object> entry : params.entrySet()) {
                urlBuilder.addQueryParameter(entry.getKey(), entry.getValue().toString());
            }
        }

        Request.Builder requestBuilder = new Request.Builder()
            .url(urlBuilder.build())
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .header("User-Agent", "{title}-SDK/1.0");
        {auth_header}

        if ("POST".equals(method) || "PUT".equals(method)) {
            MediaType jsonType = MediaType.parse("application/json; charset=utf-8");
            RequestBody body = RequestBody.create(objectMapper.writeValueAsString(data), jsonType);
            requestBuilder.method(method, body);
        } else {
            requestBuilder.method(method, null);
        }

        Response response = client.newCall(requestBuilder.build()).execute();
        if (!response.isSuccessful()) {
            throw new IOException("HTTP " + response.code() + ": " + response.message());
        }

        String responseBody = response.body().string();
        return objectMapper.readValue(responseBody, Map.class);
    }

    {methods}

    public static void main(String[] args) throws IOException {
        {client_class} client = new {client_class}();
        Map<String, Object> result = client.{main_method}({params_example});
        System.out.println("响应: " + result);
    }
}
'''

# ==================== 方法模板 ====================

METHOD_TEMPLATE_PYTHON = '''
    def {method_name}(self, {params}) -> Dict:
        """
        {description}

        Args:
            {params_docs}

        Returns:
            API响应数据
        """
        return self._request(
            method='{http_method}',
            endpoint='{endpoint}',
            params={params_dict},
            data={data_dict}
        )
'''

METHOD_TEMPLATE_JS = '''
    /**
     * {description}
     * @param {params_docs}
     * @returns {Promise<object>} API响应
     */
    async {method_name}({params}) {
        return await this.request(
            '{http_method}',
            '{endpoint}',
            {params_dict},
            {data_dict}
        );
    }
'''

METHOD_TEMPLATE_JAVA = '''
    /**
     * {description}
     * {params_docs}
     * @return API响应
     */
    public Map<String, Object> {method_name}({params}) throws IOException {
        Map<String, Object> paramsMap = new HashMap<>();
        {params_map_put}
        return request('{http_method}', '{endpoint}', paramsMap, {data_dict});
    }
'''


def generate_api_sdk(
    api_url: str,
    title: str,
    language: str = 'python',
    method: str = 'GET',
    endpoints: List[Dict] = None,
    auth_type: str = 'none',
    auth_config: Dict = None
) -> str:
    """
    生成API调用SDK

    Args:
        api_url: API基础URL
        title: SDK标题
        language: 目标语言（python/javascript/java）
        method: 主请求方法
        endpoints: API端点配置列表
        auth_type: 认证类型（none/api_key/token/basic）
        auth_config: 认证配置

    Returns:
        生成的SDK代码
    """
    generated_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 解析base_url
    from urllib.parse import urlparse
    parsed = urlparse(api_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    module_name = title.lower().replace(' ', '_').replace('-', '_') + '_sdk'
    client_class = title.replace(' ', '').replace('-', '') + 'Client'

    # 认证设置
    auth_setup = ''
    auth_field = ''
    auth_init = ''
    auth_header = ''

    if auth_type == 'api_key':
        auth_setup = f"self.session.headers.update({'X-API-Key': '{auth_config.get('key', 'YOUR_API_KEY')}'})"
        auth_field = f"private final String apiKey = \"{auth_config.get('key', 'YOUR_API_KEY')}\";"
        auth_header = "requestBuilder.header(\"X-API-Key\", apiKey);"
    elif auth_type == 'token':
        auth_setup = f"self.session.headers.update({'Authorization': 'Bearer YOUR_TOKEN'})"
        auth_field = "private final String token = \"YOUR_TOKEN\";"
        auth_header = "requestBuilder.header(\"Authorization\", \"Bearer \" + token);"

    # 生成方法
    methods = ''
    main_method = 'getData'
    params_example = ''

    if endpoints:
        for ep in endpoints[:1]:  # 取第一个作为主方法
            main_method = ep.get('name', 'getData')
            params_example = ', '.join([f"{p}='test'" for p in ep.get('params', [])])

    if language == 'python':
        return PYTHON_SDK_TEMPLATE.format(
            title=title,
            api_url=api_url,
            generated_time=generated_time,
            method=method,
            auth_type=auth_type,
            module_name=module_name,
            client_class=client_class,
            base_url=base_url,
            auth_setup=auth_setup,
            methods=methods,
            main_method=main_method,
            params_example=params_example
        )
    elif language == 'javascript':
        return JS_SDK_TEMPLATE.format(
            title=title,
            api_url=api_url,
            generated_time=generated_time,
            method=method,
            client_class=client_class,
            base_url=base_url,
            auth_setup=auth_setup,
            methods=methods,
            main_method=main_method,
            params_example=params_example
        )
    elif language == 'java':
        return JAVA_SDK_TEMPLATE.format(
            title=title,
            api_url=api_url,
            generated_time=generated_time,
            client_class=client_class,
            base_url=base_url,
            auth_field=auth_field,
            auth_init=auth_init,
            auth_header=auth_header,
            methods=methods,
            main_method=main_method,
            params_example=params_example
        )

    return ''


if __name__ == '__main__':
    # 测试生成Python SDK
    test_code = generate_api_sdk(
        api_url='https://api.example.com/v1',
        title='Example API',
        language='python',
        method='GET',
        endpoints=[
            {'name': 'getProducts', 'endpoint': 'products', 'params': ['page', 'limit']}
        ]
    )
    print(test_code)