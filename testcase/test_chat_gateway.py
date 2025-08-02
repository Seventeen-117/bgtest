# coding: utf-8
# @Author: bgtech
import pytest
import allure
from common.get_caseparams import read_test_data
from utils.http_utils import http_post
from utils.allure_utils import (
    step, attach_test_data, attach_json, attach_text,
    http_request_with_allure
)
from common.log import info, error

# 读取yaml测试数据
test_data = read_test_data('caseparams/test_chat_gateway.yaml')

@pytest.mark.parametrize("case", test_data)
@allure.feature("聊天网关")
@allure.story("API测试")
def test_chat_gateway(case):
    """聊天网关测试用例"""
    
    case_id = case.get('case_id', 'Unknown')
    description = case.get('description', 'No description')
    url = case['url']
    method = case['method'].upper()
    params = case.get('params', {})
    expected = case.get('expected_result', {})

    with allure.step(f"执行用例: {case_id} - {description}"):
        # 附加测试用例信息
        attach_test_data(case, f"测试用例: {case_id}")
        
        with step("准备请求参数"):
            info(f"请求地址: {url}")
            info(f"请求参数: {params}")
            attach_json(params, "请求参数")

        with step("发送HTTP请求"):
            try:
                if method == 'POST':
                    # 使用增强的HTTP请求函数
                    resp = http_request_with_allure(
                        method="POST",
                        url=url,
                        json_data=params
                    )
                else:
                    error(f"暂不支持的请求方式: {method}")
                    pytest.skip("暂不支持的请求方式")

                info(f"接口返回: {resp}")
                attach_json(resp, "接口响应")

            except Exception as e:
                attach_text(f"请求失败: {str(e)}", "错误信息")
                raise

        with step("验证响应结果"):
            # 断言
            for k, v in expected.items():
                actual_value = resp.get(k)
                assert actual_value == v, f"断言失败: {k} 期望: {v} 实际: {actual_value}"
                attach_text(f"断言通过: {k} = {actual_value}", "断言结果")
            
            attach_text("所有断言验证通过", "验证结果")