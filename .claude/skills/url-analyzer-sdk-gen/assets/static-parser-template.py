#!/usr/bin/env python3
"""
静态页面解析SDK模板
用于生成静态HTML页面的数据解析代码

基于此模板生成的SDK将包含：
- HTTP请求逻辑
- HTML解析逻辑
- 数据提取规则
- 错误处理
- 使用示例
"""

# ==================== SDK模板 ====================

STATIC_PARSER_TEMPLATE = '''
#!/usr/bin/env python3
"""
{title} - 静态页面数据解析SDK

源URL: {source_url}
生成时间: {generated_time}
解析区域: {parse_region}

使用示例:
    from {module_name} import {parser_class}

    parser = {parser_class}()
    data = parser.parse()
    print(data)
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class {parser_class}:
    """静态页面数据解析器"""

    def __init__(self, timeout: int = 30, retry_times: int = 3):
        """
        初始化解析器

        Args:
            timeout: 请求超时时间（秒）
            retry_times: 重试次数
        """
        self.source_url = "{source_url}"
        self.timeout = timeout
        self.retry_times = retry_times
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        })

    def _fetch_html(self) -> str:
        """
        获取HTML内容，带重试机制

        Returns:
            HTML文本内容

        Raises:
            requests.RequestException: 请求失败
        """
        for attempt in range(self.retry_times):
            try:
                response = self.session.get(self.source_url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or 'utf-8'
                logger.info(f"成功获取页面: {self.source_url}")
                return response.text
            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.retry_times}): {e}")
                if attempt < self.retry_times - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise

    def _parse_html(self, html: str) -> {return_type}:
        """
        解析HTML并提取数据

        Args:
            html: HTML文本内容

        Returns:
            解析后的数据
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # 解析区域配置
        {parse_logic}

        return results

    def parse(self) -> {return_type}:
        """
        执行完整解析流程

        Returns:
            解析后的数据列表/字典
        """
        try:
            html = self._fetch_html()
            data = self._parse_html(html)
            logger.info(f"解析完成，获取 {len(data) if isinstance(data, list) else 1} 条数据")
            return data
        except Exception as e:
            logger.error(f"解析失败: {e}")
            raise

    def close(self):
        """关闭会话"""
        self.session.close()


# 使用示例
if __name__ == '__main__':
    parser = {parser_class}()
    try:
        data = parser.parse()
        # 打印前5条数据示例
        if isinstance(data, list):
            for i, item in enumerate(data[:5]):
                print(f"数据 {i + 1}: {item}")
        else:
            print(f"解析结果: {data}")
    finally:
        parser.close()
'''

# ==================== 解析逻辑模板 ====================

PARSE_LOGIC_TEMPLATES = {
    'css_selector': '''
        # 使用CSS选择器定位元素
        items = soup.select('{selector}')

        for item in items:
            result = {}
            {field_mappings}
            results.append(result)
    ''',

    'xpath': '''
        # 注意：BeautifulSoup不支持XPath，需要使用lxml
        from lxml import etree
        tree = etree.HTML(html)
        items = tree.xpath('{xpath}')

        for item in items:
            result = {}
            {field_mappings}
            results.append(result)
    ''',

    'table': '''
        # 解析表格数据
        table = soup.find('table', {'class': '{table_class}'})
        if table:
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            for row in table.find_all('tr')[1:]:  # 跳过表头
                cells = [td.get_text(strip=True) for td in row.find_all('td')]
                if cells:
                    results.append(dict(zip(headers, cells)))
    ''',

    'list': '''
        # 解析列表数据
        list_container = soup.find('{list_tag}', {'class': '{list_class}'})
        if list_container:
            items = list_container.find_all('{item_tag}')
            for item in items:
                result = {
                    'title': item.find('{title_tag}').get_text(strip=True) if item.find('{title_tag}') else None,
                    'link': item.find('a')['href'] if item.find('a') else None,
                    'description': item.find('{desc_tag}').get_text(strip=True) if item.find('{desc_tag}') else None
                }
                results.append(result)
    '''
}

# ==================== 字段映射模板 ====================

FIELD_MAPPING_TEMPLATE = '''
result['{field_name}'] = item.find('{element_tag}').get_text(strip=True) if item.find('{element_tag}') else None
'''

FIELD_MAPPING_ATTRIBUTE_TEMPLATE = '''
result['{field_name}'] = item.find('{element_tag}').get('{attribute}') if item.find('{element_tag}') else None
'''


def generate_static_parser(
    source_url: str,
    title: str,
    parse_region: str,
    selector_type: str = 'css_selector',
    selector: str = '',
    fields: List[Dict] = None,
    return_type: str = 'List[Dict]'
) -> str:
    """
    生成静态页面解析SDK代码

    Args:
        source_url: 源URL
        title: SDK标题
        parse_region: 解析区域描述
        selector_type: 选择器类型（css_selector/xpath/table/list）
        selector: 选择器表达式
        fields: 字段映射配置
        return_type: 返回类型声明

    Returns:
        生成的SDK代码
    """
    import datetime

    # 生成模块名和类名
    module_name = title.lower().replace(' ', '_').replace('-', '_') + '_sdk'
    parser_class = title.replace(' ', '').replace('-', '') + 'Parser'

    # 生成字段映射代码
    field_mappings = ''
    if fields:
        for field in fields:
            if 'attribute' in field:
                field_mappings += FIELD_MAPPING_ATTRIBUTE_TEMPLATE.format(
                    field_name=field['name'],
                    element_tag=field['tag'],
                    attribute=field['attribute']
                )
            else:
                field_mappings += FIELD_MAPPING_TEMPLATE.format(
                    field_name=field['name'],
                    element_tag=field['tag']
                )

    # 生成解析逻辑
    parse_logic = PARSE_LOGIC_TEMPLATES.get(selector_type, PARSE_LOGIC_TEMPLATES['css_selector']).format(
        selector=selector,
        field_mappings=field_mappings,
        table_class=selector if selector_type == 'table' else '',
        list_tag=fields[0].get('container_tag', 'ul') if fields else 'ul',
        list_class=selector,
        item_tag=fields[0].get('item_tag', 'li') if fields else 'li',
        title_tag=fields[0].get('title_tag', 'a') if fields else 'a',
        desc_tag=fields[0].get('desc_tag', 'p') if fields else 'p',
        xpath=selector if selector_type == 'xpath' else ''
    )

    # 生成完整代码
    code = STATIC_PARSER_TEMPLATE.format(
        title=title,
        source_url=source_url,
        generated_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        parse_region=parse_region,
        module_name=module_name,
        parser_class=parser_class,
        return_type=return_type,
        parse_logic=parse_logic
    )

    return code


# ==================== 测试示例 ====================

if __name__ == '__main__':
    # 示例：生成一个博客文章解析器
    test_code = generate_static_parser(
        source_url='https://example.com/blog',
        title='Blog Posts Parser',
        parse_region='所有文章标题和链接',
        selector_type='css_selector',
        selector='.post-item',
        fields=[
            {'name': 'title', 'tag': 'h2'},
            {'name': 'link', 'tag': 'a', 'attribute': 'href'},
            {'name': 'summary', 'tag': 'p'}
        ]
    )
    print(test_code)