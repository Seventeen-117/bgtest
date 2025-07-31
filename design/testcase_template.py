# pytest用例生成模板

def generate_pytest_case(case_name, url, method, params, expected):
    """
    生成pytest用例代码字符串
    :param case_name: 用例名
    :param url: 接口地址
    :param method: 请求方法（GET/POST）
    :param params: 请求参数（字典）
    :param expected: 期望结果（字典）
    :return: pytest用例代码字符串
    """
    return f"""
import pytest
from utils.http_utils import http_{method.lower()}

def test_{case_name}():
    resp = http_{method.lower()}('{url}', params={params})
    assert resp == {expected}
"""

# 示例用法：
# code = generate_pytest_case('demo', 'http://localhost', 'GET', {'a':1}, {'code':0})
# print(code) 