# coding: utf-8
# @Author: bgtech
from common.log import api_info, api_error
import re
import json
from typing import Any, Dict, List, Union

def assert_equal(actual, expected, msg=None):
    """
    断言实际值等于期望值
    """
    try:
        assert actual == expected
        api_info(f"断言通过: {actual} == {expected}")
    except AssertionError:
        error_msg = msg or f"断言失败: 期望 {expected}, 实际 {actual}"
        api_error(error_msg)
        raise AssertionError(error_msg)

def assert_in(item, container, msg=None):
    """
    断言item在container中
    """
    try:
        assert item in container
        api_info(f"断言通过: {item} 在 {container} 中")
    except AssertionError:
        error_msg = msg or f"断言失败: {item} 不在 {container} 中"
        api_error(error_msg)
        raise AssertionError(error_msg)

def assert_contains(container, item, msg=None):
    """
    断言container包含item
    """
    try:
        assert item in container
        api_info(f"断言通过: {container} 包含 {item}")
    except AssertionError:
        error_msg = msg or f"断言失败: {container} 不包含 {item}"
        api_error(error_msg)
        raise AssertionError(error_msg)

def assert_regex_match(pattern, text, msg=None):
    """
    断言文本匹配正则表达式
    """
    try:
        assert re.search(pattern, text)
        api_info(f"断言通过: 文本匹配正则 {pattern}")
    except AssertionError:
        error_msg = msg or f"断言失败: 文本不匹配正则 {pattern}"
        api_error(error_msg)
        raise AssertionError(error_msg)

def assert_json_structure(response, expected_structure):
    """
    断言JSON响应结构
    """
    try:
        for key in expected_structure:
            assert key in response, f"响应中缺少字段: {key}"
        api_info(f"断言通过: JSON结构验证成功")
    except AssertionError as e:
        api_error(f"断言失败: {e}")
        raise

def assert_status_code(response, expected_code):
    """
    断言HTTP状态码
    """
    try:
        actual_code = response.get('status_code', 200)
        assert actual_code == expected_code
        api_info(f"断言通过: 状态码 {actual_code} == {expected_code}")
    except AssertionError:
        error_msg = f"断言失败: 状态码期望 {expected_code}, 实际 {actual_code}"
        api_error(error_msg)
        raise AssertionError(error_msg)

def assert_response_time(response, max_time):
    """
    断言响应时间不超过最大值（毫秒）
    """
    try:
        response_time = response.get('response_time', 0)
        assert response_time <= max_time
        api_info(f"断言通过: 响应时间 {response_time}ms <= {max_time}ms")
    except AssertionError:
        error_msg = f"断言失败: 响应时间 {response_time}ms > {max_time}ms"
        api_error(error_msg)
        raise AssertionError(error_msg)


class AssertionUtils:
    """断言工具类，提供各种断言方法"""
    
    def __init__(self):
        self.assertion_count = 0
        self.passed_count = 0
        self.failed_count = 0
    
    def assert_equal(self, actual: Any, expected: Any, msg: str = None) -> bool:
        """断言实际值等于期望值"""
        self.assertion_count += 1
        try:
            assert actual == expected
            self.passed_count += 1
            api_info(f"断言通过: {actual} == {expected}")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = msg or f"断言失败: 期望 {expected}, 实际 {actual}"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_in(self, item: Any, container: Any, msg: str = None) -> bool:
        """断言item在container中"""
        self.assertion_count += 1
        try:
            assert item in container
            self.passed_count += 1
            api_info(f"断言通过: {item} 在 {container} 中")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = msg or f"断言失败: {item} 不在 {container} 中"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_contains(self, container: Any, item: Any, msg: str = None) -> bool:
        """断言container包含item"""
        self.assertion_count += 1
        try:
            assert item in container
            self.passed_count += 1
            api_info(f"断言通过: {container} 包含 {item}")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = msg or f"断言失败: {container} 不包含 {item}"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_regex_match(self, pattern: str, text: str, msg: str = None) -> bool:
        """断言文本匹配正则表达式"""
        self.assertion_count += 1
        try:
            assert re.search(pattern, text)
            self.passed_count += 1
            api_info(f"断言通过: 文本匹配正则 {pattern}")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = msg or f"断言失败: 文本不匹配正则 {pattern}"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_json_structure(self, response: Dict[str, Any], expected_structure: List[str]) -> bool:
        """断言JSON响应结构"""
        self.assertion_count += 1
        try:
            for key in expected_structure:
                assert key in response, f"响应中缺少字段: {key}"
            self.passed_count += 1
            api_info(f"断言通过: JSON结构验证成功")
            return True
        except AssertionError as e:
            self.failed_count += 1
            api_error(f"断言失败: {e}")
            raise
    
    def assert_status_code(self, response: Union[Dict[str, Any], Any], expected_code: int) -> bool:
        """断言HTTP状态码"""
        self.assertion_count += 1
        try:
            if isinstance(response, dict):
                actual_code = response.get('status_code', 200)
            else:
                # 假设response是requests.Response对象
                actual_code = getattr(response, 'status_code', 200)
            
            assert actual_code == expected_code
            self.passed_count += 1
            api_info(f"断言通过: 状态码 {actual_code} == {expected_code}")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = f"断言失败: 状态码期望 {expected_code}, 实际 {actual_code}"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_response_time(self, response: Union[Dict[str, Any], Any], max_time: int) -> bool:
        """断言响应时间不超过最大值（毫秒）"""
        self.assertion_count += 1
        try:
            if isinstance(response, dict):
                response_time = response.get('response_time', 0)
            else:
                # 假设response是requests.Response对象
                response_time = getattr(response, 'elapsed', 0)
                if hasattr(response_time, 'total_seconds'):
                    response_time = response_time.total_seconds() * 1000
                else:
                    response_time = 0
            
            assert response_time <= max_time
            self.passed_count += 1
            api_info(f"断言通过: 响应时间 {response_time}ms <= {max_time}ms")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = f"断言失败: 响应时间 {response_time}ms > {max_time}ms"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_response_contains(self, response: Union[Dict[str, Any], str], expected_text: str) -> bool:
        """断言响应包含指定文本"""
        self.assertion_count += 1
        try:
            if isinstance(response, dict):
                response_text = json.dumps(response, ensure_ascii=False)
            else:
                response_text = str(response)
            
            assert expected_text in response_text
            self.passed_count += 1
            api_info(f"断言通过: 响应包含文本 {expected_text}")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = f"断言失败: 响应不包含文本 {expected_text}"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_not_none(self, value: Any, msg: str = None) -> bool:
        """断言值不为None"""
        self.assertion_count += 1
        try:
            assert value is not None
            self.passed_count += 1
            api_info(f"断言通过: 值不为None")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = msg or f"断言失败: 值为None"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_true(self, condition: bool, msg: str = None) -> bool:
        """断言条件为True"""
        self.assertion_count += 1
        try:
            assert condition
            self.passed_count += 1
            api_info(f"断言通过: 条件为True")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = msg or f"断言失败: 条件为False"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def assert_false(self, condition: bool, msg: str = None) -> bool:
        """断言条件为False"""
        self.assertion_count += 1
        try:
            assert not condition
            self.passed_count += 1
            api_info(f"断言通过: 条件为False")
            return True
        except AssertionError:
            self.failed_count += 1
            error_msg = msg or f"断言失败: 条件为True"
            api_error(error_msg)
            raise AssertionError(error_msg)
    
    def get_assertion_stats(self) -> Dict[str, int]:
        """获取断言统计信息"""
        return {
            'total': self.assertion_count,
            'passed': self.passed_count,
            'failed': self.failed_count,
            'success_rate': (self.passed_count / self.assertion_count * 100) if self.assertion_count > 0 else 0
        }
    
    def reset_stats(self):
        """重置断言统计"""
        self.assertion_count = 0
        self.passed_count = 0
        self.failed_count = 0