# coding: utf-8
# @Author: bgtech
import pytest
from common.get_caseparams import read_test_data
from utils.http_utils import http_post
from common.log import info, error

# 读取yaml测试数据
test_data = read_test_data('caseparams/test_chat_gateway.yaml')

@pytest.mark.parametrize("case", test_data)
def test_chat_gateway(case):
    url = case['url']
    method = case['method'].upper()
    params = case.get('params', {})
    expected = case.get('expected_result', {})

    info(f"执行用例: {case['case_id']} - {case['description']}")
    info(f"请求地址: {url}")
    info(f"请求参数: {params}")

    if method == 'POST':
        resp = http_post(url, json_data=params)
    else:
        error(f"暂不支持的请求方式: {method}")
        pytest.skip("暂不支持的请求方式")

    info(f"接口返回: {resp}")

    # 断言
    for k, v in expected.items():
        assert resp.get(k) == v, f"断言失败: {k} 期望: {v} 实际: {resp.get(k)}"