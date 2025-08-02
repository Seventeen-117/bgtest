# coding: utf-8
# @Author: bgtech
"""
测试用例工具类
提供常用的测试方法，供testcase下的测试用例使用
"""

import json
import re
import pytest
import allure
from typing import Dict, Any, List, Union, Optional
from common.log import info, error, api_info, api_error
from common.assertion import AssertionUtils
from utils.allure_utils import (
    step, attach_test_data, attach_json, attach_text,
    http_request_with_allure
)
from utils.http_utils import http_get, http_post
from common.data_source import get_test_data_from_file, get_all_test_data


class TestCaseUtils:
    """测试用例工具类"""
    
    def __init__(self):
        self.assertion_utils = AssertionUtils()
    
    def parse_json_safely(self, json_input: Any) -> Dict[str, Any]:
        """
        安全解析JSON，支持字符串、字典等多种输入格式
        :param json_input: JSON输入
        :return: 解析后的字典
        """
        # 如果输入已经是字典，直接返回
        if isinstance(json_input, dict):
            return json_input
        
        # 如果输入为空或空字符串，返回空字典
        if not json_input or json_input == '{}':
            return {}
        
        # 如果输入是字符串，尝试解析JSON
        if isinstance(json_input, str):
            try:
                return json.loads(json_input)
            except json.JSONDecodeError as e:
                error(f"JSON解析失败: {json_input}, 错误: {e}")
                
                # 尝试多种清理方式
                cleaned_str = json_input
                
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
                    return {}
        
        # 其他类型，返回空字典
        error(f"不支持的输入类型: {type(json_input)}, 值: {json_input}")
        return {}
    
    def execute_http_request(self, url: str, method: str, params: Dict[str, Any] = None, 
                           headers: Dict[str, Any] = None, use_allure: bool = True) -> Dict[str, Any]:
        """
        执行HTTP请求
        :param url: 请求URL
        :param method: 请求方法
        :param params: 请求参数
        :param headers: 请求头
        :param use_allure: 是否使用Allure增强
        :return: 响应结果
        """
        method = method.upper()
        params = params or {}
        headers = headers or {}
        
        with step(f"发送{method}请求到 {url}"):
            try:
                if use_allure:
                    # 使用Allure增强的HTTP请求
                    if method == 'GET':
                        resp = http_request_with_allure(
                            method="GET",
                            url=url,
                            params=params,
                            headers=headers
                        )
                    elif method == 'POST':
                        resp = http_request_with_allure(
                            method="POST",
                            url=url,
                            json_data=params,
                            headers=headers
                        )
                    else:
                        error(f"暂不支持的请求方式: {method}")
                        pytest.skip("暂不支持的请求方式")
                else:
                    # 使用普通HTTP请求
                    if method == 'GET':
                        resp = http_get(url, params=params, headers=headers)
                    elif method == 'POST':
                        resp = http_post(url, json_data=params, headers=headers)
                    else:
                        error(f"暂不支持的请求方式: {method}")
                        pytest.skip("暂不支持的请求方式")
                
                info(f"接口返回: {resp}")
                attach_json(resp, "接口响应")
                return resp
                
            except Exception as e:
                error_msg = f"请求失败: {str(e)}"
                attach_text(error_msg, "错误信息")
                raise Exception(error_msg)
    
    def validate_response(self, response: Dict[str, Any], expected: Dict[str, Any], 
                         case_id: str = "Unknown") -> bool:
        """
        验证响应结果
        :param response: 实际响应
        :param expected: 期望结果
        :param case_id: 用例ID
        :return: 验证是否通过
        """
        with step(f"验证响应结果 - {case_id}"):
            try:
                validation_passed = True
                
                for key, expected_value in expected.items():
                    actual_value = response.get(key)
                    
                    if not self.assertion_utils.assert_equal(actual_value, expected_value, 
                                                           f"字段 {key} 验证失败"):
                        validation_passed = False
                        attach_text(f"断言失败: {key} 期望: {expected_value} 实际: {actual_value}", 
                                  "验证失败")
                    else:
                        attach_text(f"断言通过: {key} = {actual_value}", "验证成功")
                
                if validation_passed:
                    attach_text("所有断言验证通过", "验证结果")
                    info(f"用例 {case_id} 验证通过")
                else:
                    error(f"用例 {case_id} 验证失败")
                
                return validation_passed
                
            except Exception as e:
                error_msg = f"验证过程发生异常: {str(e)}"
                attach_text(error_msg, "验证异常")
                raise Exception(error_msg)
    
    def validate_response_structure(self, response: Dict[str, Any], 
                                  expected_structure: List[str], case_id: str = "Unknown") -> bool:
        """
        验证响应结构
        :param response: 实际响应
        :param expected_structure: 期望的字段列表
        :param case_id: 用例ID
        :return: 验证是否通过
        """
        with step(f"验证响应结构 - {case_id}"):
            try:
                return self.assertion_utils.assert_json_structure(response, expected_structure)
            except Exception as e:
                error_msg = f"结构验证失败: {str(e)}"
                attach_text(error_msg, "结构验证失败")
                raise Exception(error_msg)
    
    def validate_response_contains(self, response: Dict[str, Any], 
                                 expected_text: str, case_id: str = "Unknown") -> bool:
        """
        验证响应包含指定文本
        :param response: 实际响应
        :param expected_text: 期望包含的文本
        :param case_id: 用例ID
        :return: 验证是否通过
        """
        with step(f"验证响应包含文本 - {case_id}"):
            try:
                response_str = json.dumps(response, ensure_ascii=False)
                return self.assertion_utils.assert_response_contains(response_str, expected_text)
            except Exception as e:
                error_msg = f"文本包含验证失败: {str(e)}"
                attach_text(error_msg, "文本验证失败")
                raise Exception(error_msg)
    
    def load_test_data(self, file_path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        加载测试数据
        :param file_path: 文件路径
        :param encoding: 文件编码
        :return: 测试数据列表
        """
        try:
            return get_test_data_from_file(file_path, encoding)
        except Exception as e:
            error(f"加载测试数据失败: {e}")
            return []
    
    def load_all_test_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        加载所有测试数据
        :return: 测试数据字典
        """
        try:
            return get_all_test_data()
        except Exception as e:
            error(f"加载所有测试数据失败: {e}")
            return {}
    
    def prepare_test_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备测试用例数据
        :param case: 原始用例数据
        :return: 处理后的用例数据
        """
        case_id = case.get('case_id', 'Unknown')
        description = case.get('description', 'No description')
        url = case.get('url', '')
        method = case.get('method', 'GET').upper()
        params = self.parse_json_safely(case.get('params', '{}'))
        expected = self.parse_json_safely(case.get('expected_result', '{}'))
        headers = self.parse_json_safely(case.get('headers', '{}'))
        
        return {
            'case_id': case_id,
            'description': description,
            'url': url,
            'method': method,
            'params': params,
            'expected': expected,
            'headers': headers
        }
    
    def execute_test_case(self, case: Dict[str, Any], use_allure: bool = True) -> bool:
        """
        执行单个测试用例
        :param case: 测试用例数据
        :param use_allure: 是否使用Allure增强
        :return: 测试是否通过
        """
        case_data = self.prepare_test_case(case)
        
        with allure.step(f"执行用例: {case_data['case_id']} - {case_data['description']}"):
            # 附加测试用例信息
            attach_test_data(case_data, f"测试用例: {case_data['case_id']}")
            
            with step("准备请求参数"):
                info(f"请求地址: {case_data['url']}")
                info(f"请求参数: {case_data['params']}")
                attach_json(case_data['params'], "请求参数")
            
            # 执行HTTP请求
            response = self.execute_http_request(
                url=case_data['url'],
                method=case_data['method'],
                params=case_data['params'],
                headers=case_data['headers'],
                use_allure=use_allure
            )
            
            # 验证响应结果
            return self.validate_response(response, case_data['expected'], case_data['case_id'])
    
    def get_assertion_stats(self) -> Dict[str, int]:
        """
        获取断言统计信息
        :return: 断言统计字典
        """
        return self.assertion_utils.get_assertion_stats()
    
    def reset_assertion_stats(self):
        """重置断言统计"""
        self.assertion_utils.reset_stats()


# 全局测试工具实例
test_utils = TestCaseUtils()

# 便捷函数
def parse_json_safely(json_input: Any) -> Dict[str, Any]:
    """安全解析JSON的便捷函数"""
    return test_utils.parse_json_safely(json_input)

def execute_http_request(url: str, method: str, params: Dict[str, Any] = None, 
                        headers: Dict[str, Any] = None, use_allure: bool = True) -> Dict[str, Any]:
    """执行HTTP请求的便捷函数"""
    return test_utils.execute_http_request(url, method, params, headers, use_allure)

def validate_response(response: Dict[str, Any], expected: Dict[str, Any], 
                     case_id: str = "Unknown") -> bool:
    """验证响应结果的便捷函数"""
    return test_utils.validate_response(response, expected, case_id)

def validate_response_structure(response: Dict[str, Any], 
                              expected_structure: List[str], case_id: str = "Unknown") -> bool:
    """验证响应结构的便捷函数"""
    return test_utils.validate_response_structure(response, expected_structure, case_id)

def validate_response_contains(response: Dict[str, Any], 
                             expected_text: str, case_id: str = "Unknown") -> bool:
    """验证响应包含指定文本的便捷函数"""
    return test_utils.validate_response_contains(response, expected_text, case_id)

def load_test_data(file_path: str, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
    """加载测试数据的便捷函数"""
    return test_utils.load_test_data(file_path, encoding)

def load_all_test_data() -> Dict[str, List[Dict[str, Any]]]:
    """加载所有测试数据的便捷函数"""
    return test_utils.load_all_test_data()

def prepare_test_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """准备测试用例数据的便捷函数"""
    return test_utils.prepare_test_case(case)

def execute_test_case(case: Dict[str, Any], use_allure: bool = True) -> bool:
    """执行单个测试用例的便捷函数"""
    return test_utils.execute_test_case(case, use_allure)

def get_assertion_stats() -> Dict[str, int]:
    """获取断言统计信息的便捷函数"""
    return test_utils.get_assertion_stats()

def reset_assertion_stats():
    """重置断言统计的便捷函数"""
    test_utils.reset_assertion_stats() 