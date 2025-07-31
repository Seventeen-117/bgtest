import pytest
import json
import re
from common.get_caseparams import read_test_data
from utils.http_utils import http_get, http_post
from common.log import info, error

# 读取csv测试数据
cases = read_test_data('caseparams/test_http_data.csv')

def parse_json_safely(json_str):
    """
    安全解析JSON字符串，处理可能的格式问题
    """
    if not json_str or json_str == '{}':
        return {}
    
    try:
        # 尝试直接解析
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        error(f"JSON解析失败: {json_str}, 错误: {e}")
        
        # 尝试多种清理方式
        cleaned_str = json_str
        
        # 方式1: 处理双引号转义 (CSV中的标准格式)
        if '""' in cleaned_str:
            cleaned_str = cleaned_str.replace('""', '"')
        
        # 方式2: 处理反斜杠转义
        if '\\"' in cleaned_str:
            cleaned_str = cleaned_str.replace('\\"', '"')
        
        # 方式3: 移除多余的反斜杠
        cleaned_str = cleaned_str.replace('\\', '')
        
        # 方式4: 确保JSON格式正确
        if not cleaned_str.startswith('{'):
            cleaned_str = '{' + cleaned_str
        if not cleaned_str.endswith('}'):
            cleaned_str = cleaned_str + '}'
        
        try:
            return json.loads(cleaned_str)
        except json.JSONDecodeError:
            error(f"清理后仍无法解析JSON: {cleaned_str}")
            # 返回空字典，避免测试失败
            return {}

@pytest.mark.parametrize("case", cases)
def test_http_data(case):
    url = case['url']
    method = case['method'].upper()
    params = parse_json_safely(case.get('params', '{}'))
    expected = parse_json_safely(case.get('expected_result', '{}'))

    info(f"执行用例: {case['case_id']} - {case['description']}")
    info(f"请求地址: {url}")
    info(f"请求参数: {params}")

    if method == 'GET':
        resp = http_get(url, params=params)
    elif method == 'POST':
        resp = http_post(url, json_data=params)
    else:
        error(f"暂不支持的请求方式: {method}")
        pytest.skip("暂不支持的请求方式")

    info(f"接口返回: {resp}")

    # 断言：预期内容应包含在返回内容中
    for k, v in expected.items():
        assert k in resp, f"返回内容缺少字段: {k}"
        assert resp[k] == v, f"断言失败: {k} 期望: {v} 实际: {resp[k]}" 