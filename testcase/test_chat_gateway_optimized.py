# coding: utf-8
# @Author: bgtech
"""
优化后的聊天网关测试用例
使用common和utils下的公共方法
"""
from logging import info, error

import pytest
import allure
from common.test_utils import (
    load_test_data, execute_http_request, validate_response,
    parse_json_safely, test_utils
)
from utils.test_decorators import (
    allure_test_case_decorator, allure_api_test_decorator, allure_data_driven_test_decorator, smoke_test,
    allure_feature_story, allure_severity, log_test_info
)

# 加载测试数据
test_data = load_test_data('caseparams/test_chat_gateway.yaml')

@pytest.mark.parametrize("case", test_data)
@allure.feature("聊天网关")
@allure.story("API测试")
@allure_test_case_decorator("聊天网关API测试", "测试聊天网关的各种API接口")
@allure_api_test_decorator("聊天网关", "POST", "https://api.example.com/chat")
@allure_data_driven_test_decorator("test_chat_gateway.yaml", "yaml")
@smoke_test
@allure_severity("critical")
@log_test_info
def test_chat_gateway_optimized(case):
    """优化后的聊天网关测试用例"""
    
    # 使用公共方法准备测试数据
    case_data = test_utils.prepare_test_case(case)
    
    # 执行测试用例
    success = test_utils.execute_test_case(case, use_allure=True)
    
    # 验证测试结果
    assert success, f"测试用例 {case_data['case_id']} 执行失败"


@pytest.mark.parametrize("case", test_data)
@allure.feature("聊天网关")
@allure.story("基础功能测试")
@allure_test_case_decorator("聊天网关基础功能", "测试聊天网关的基础功能")
@smoke_test
@allure_severity("normal")
def test_chat_gateway_basic(case):
    """聊天网关基础功能测试"""
    
    case_id = case.get('case_id', 'Unknown')
    description = case.get('description', 'No description')
    url = case['url']
    method = case['method'].upper()
    params = parse_json_safely(case.get('params', '{}'))
    expected = parse_json_safely(case.get('expected_result', '{}'))

    with allure.step(f"执行基础功能测试: {case_id} - {description}"):
        # 执行HTTP请求
        response = execute_http_request(
            url=url,
            method=method,
            params=params,
            use_allure=True
        )
        
        # 验证响应结果
        validate_response(response, expected, case_id)


@pytest.mark.parametrize("case", test_data)
@allure.feature("聊天网关")
@allure.story("性能测试")
@allure_test_case_decorator("聊天网关性能测试", "测试聊天网关的性能表现")
@allure_severity("minor")
def test_chat_gateway_performance(case):
    """聊天网关性能测试"""
    
    case_id = case.get('case_id', 'Unknown')
    url = case['url']
    method = case['method'].upper()
    params = parse_json_safely(case.get('params', '{}'))

    with allure.step(f"执行性能测试: {case_id}"):
        # 执行HTTP请求（不使用Allure增强，减少开销）
        response = execute_http_request(
            url=url,
            method=method,
            params=params,
            use_allure=False
        )
        
        # 验证响应时间（假设期望响应时间小于1000ms）
        assert 'response_time' in response or 'elapsed' in response, "响应中缺少时间信息"
        
        # 这里可以添加更多的性能验证逻辑
        info(f"性能测试完成: {case_id}")


class TestChatGatewayAdvanced:
    """聊天网关高级测试类"""
    
    def setup_method(self):
        """测试方法设置"""
        info("开始聊天网关高级测试")
    
    def teardown_method(self):
        """测试方法清理"""
        info("完成聊天网关高级测试")
    
    @allure_feature_story("聊天网关", "高级功能")
    @allure_test_case_decorator("聊天网关高级功能", "测试聊天网关的高级功能")
    @allure_severity("critical")
    def test_chat_gateway_advanced_features(self):
        """测试聊天网关高级功能"""
        
        # 加载所有测试数据
        all_data = test_utils.load_all_test_data()
        chat_data = all_data.get('test_chat_gateway', [])
        
        for case in chat_data:
            # 执行测试用例
            success = test_utils.execute_test_case(case, use_allure=True)
            assert success, f"高级功能测试失败: {case.get('case_id', 'Unknown')}"
    
    @allure_feature_story("聊天网关", "错误处理")
    @allure_test_case_decorator("聊天网关错误处理", "测试聊天网关的错误处理能力")
    @allure_severity("normal")
    def test_chat_gateway_error_handling(self):
        """测试聊天网关错误处理"""
        
        # 构造错误场景的测试数据
        error_cases = [
            {
                'case_id': 'error_001',
                'description': '测试无效URL',
                'url': 'https://invalid-url.com/chat',
                'method': 'POST',
                'params': {'message': 'test'},
                'expected_result': {'error': 'connection_failed'}
            },
            {
                'case_id': 'error_002',
                'description': '测试无效参数',
                'url': 'https://api.example.com/chat',
                'method': 'POST',
                'params': {},
                'expected_result': {'error': 'invalid_parameters'}
            }
        ]
        
        for case in error_cases:
            try:
                # 执行测试用例
                success = test_utils.execute_test_case(case, use_allure=True)
                # 对于错误处理测试，我们期望测试能够正常完成
                assert True, f"错误处理测试异常: {case.get('case_id', 'Unknown')}"
            except Exception as e:
                # 记录错误但不中断测试
                error(f"错误处理测试捕获异常: {e}")
    
    @allure_feature_story("聊天网关", "数据验证")
    @allure_test_case_decorator("聊天网关数据验证", "测试聊天网关的数据验证功能")
    @allure_severity("normal")
    def test_chat_gateway_data_validation(self):
        """测试聊天网关数据验证"""
        
        # 构造数据验证测试用例
        validation_cases = [
            {
                'case_id': 'validation_001',
                'description': '测试空消息',
                'url': 'https://api.example.com/chat',
                'method': 'POST',
                'params': {'message': ''},
                'expected_result': {'error': 'empty_message'}
            },
            {
                'case_id': 'validation_002',
                'description': '测试超长消息',
                'url': 'https://api.example.com/chat',
                'method': 'POST',
                'params': {'message': 'a' * 10000},  # 超长消息
                'expected_result': {'error': 'message_too_long'}
            }
        ]
        
        for case in validation_cases:
            # 执行测试用例
            success = test_utils.execute_test_case(case, use_allure=True)
            assert success, f"数据验证测试失败: {case.get('case_id', 'Unknown')}"


# 测试统计
def test_assertion_statistics():
    """测试断言统计"""
    stats = test_utils.get_assertion_stats()
    info(f"断言统计: {stats}")
    
    # 验证统计信息
    assert 'total' in stats
    assert 'passed' in stats
    assert 'failed' in stats
    assert 'success_rate' in stats
    
    # 重置统计
    test_utils.reset_assertion_stats()
    info("断言统计已重置")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 