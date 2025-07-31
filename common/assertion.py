# coding: utf-8
# @Author: bgtech
from common.log import api_info, api_error
import re
import json

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