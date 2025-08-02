# coding: utf-8
# @Author: bgtech
"""
测试装饰器工具类
提供常用的测试装饰器，供testcase下的测试用例使用
"""

import pytest
import allure
import time
from functools import wraps
from typing import Dict, Any, List, Optional, Callable
from common.log import info, error
from utils.allure_decorators import (
    allure_test_case, allure_api_test, allure_data_driven_test,
    performance_test, security_test
)


def test_case(title: str, description: str = ""):
    """
    测试用例装饰器
    :param title: 测试标题
    :param description: 测试描述
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return allure_test_case(title, description)(wrapper)
    return decorator


# 为了避免pytest误认为是fixture，添加一个别名
def allure_test_case_decorator(title: str, description: str = ""):
    """
    测试用例装饰器（别名）
    :param title: 测试标题
    :param description: 测试描述
    """
    return test_case(title, description)


def api_test(api_name: str, method: str, url: str):
    """
    API测试装饰器
    :param api_name: API名称
    :param method: 请求方法
    :param url: 请求URL
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return allure_api_test(api_name, method, url)(wrapper)
    return decorator


# 为了避免pytest误认为是fixture，添加一个别名
def allure_api_test_decorator(api_name: str, method: str, url: str):
    """
    API测试装饰器（别名）
    :param api_name: API名称
    :param method: 请求方法
    :param url: 请求URL
    """
    return api_test(api_name, method, url)


def data_driven_test(data_source: str, data_type: str = "file"):
    """
    数据驱动测试装饰器
    :param data_source: 数据源
    :param data_type: 数据类型
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return allure_data_driven_test(data_source, data_type)(wrapper)
    return decorator


# 为了避免pytest误认为是fixture，添加一个别名
def allure_data_driven_test_decorator(data_source: str, data_type: str = "file"):
    """
    数据驱动测试装饰器（别名）
    :param data_source: 数据源
    :param data_type: 数据类型
    """
    return data_driven_test(data_source, data_type)


def performance_test_decorator(threshold_ms: float = 1000.0):
    """
    性能测试装饰器
    :param threshold_ms: 性能阈值（毫秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return performance_test(threshold_ms)(wrapper)
    return decorator


def security_test_decorator(security_level: str = "medium"):
    """
    安全测试装饰器
    :param security_level: 安全级别
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return security_test(security_level)(wrapper)
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    失败重试装饰器
    :param max_retries: 最大重试次数
    :param delay: 重试间隔（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        info(f"第 {attempt} 次重试: {func.__name__}")
                        time.sleep(delay)
                    
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    error(f"第 {attempt + 1} 次执行失败: {e}")
                    
                    if attempt == max_retries:
                        error(f"达到最大重试次数 {max_retries}，停止重试")
                        raise last_exception
            
            return None
        return wrapper
    return decorator


def skip_on_condition(condition: Callable[[], bool], reason: str = "条件不满足"):
    """
    条件跳过装饰器
    :param condition: 跳过条件函数
    :param reason: 跳过原因
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if condition():
                pytest.skip(reason)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def timeout(seconds: float):
    """
    超时装饰器
    :param seconds: 超时时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"函数执行超时: {seconds}秒")
            
            # 设置信号处理器
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # 取消超时
                return result
            except TimeoutError:
                error(f"函数 {func.__name__} 执行超时")
                raise
            finally:
                signal.alarm(0)  # 确保取消超时
        
        return wrapper
    return decorator


def log_test_info(func: Callable) -> Callable:
    """
    记录测试信息的装饰器
    :param func: 被装饰的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        info(f"开始执行测试: {func.__name__}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            info(f"测试执行成功: {func.__name__}, 耗时: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error(f"测试执行失败: {func.__name__}, 耗时: {execution_time:.2f}秒, 错误: {e}")
            raise
    
    return wrapper


def validate_test_data(required_fields: List[str]):
    """
    验证测试数据的装饰器
    :param required_fields: 必需字段列表
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 检查第一个参数是否为字典（测试数据）
            if args and isinstance(args[0], dict):
                test_data = args[0]
                missing_fields = [field for field in required_fields if field not in test_data]
                
                if missing_fields:
                    error_msg = f"测试数据缺少必需字段: {missing_fields}"
                    error(error_msg)
                    pytest.fail(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def setup_teardown(setup_func: Optional[Callable] = None, 
                   teardown_func: Optional[Callable] = None):
    """
    设置和清理装饰器
    :param setup_func: 设置函数
    :param teardown_func: 清理函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 执行设置
                if setup_func:
                    info(f"执行设置: {setup_func.__name__}")
                    setup_func()
                
                # 执行测试
                result = func(*args, **kwargs)
                
                return result
            finally:
                # 执行清理
                if teardown_func:
                    info(f"执行清理: {teardown_func.__name__}")
                    teardown_func()
        
        return wrapper
    return decorator


def allure_feature_story(feature: str, story: str):
    """
    Allure特性故事装饰器
    :param feature: 特性名称
    :param story: 故事名称
    """
    def decorator(func: Callable) -> Callable:
        @allure.feature(feature)
        @allure.story(story)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def allure_severity(severity_level: str):
    """
    Allure严重程度装饰器
    :param severity_level: 严重程度 (blocker, critical, normal, minor, trivial)
    """
    def decorator(func: Callable) -> Callable:
        @allure.severity(severity_level)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def allure_description(description: str):
    """
    Allure描述装饰器
    :param description: 测试描述
    """
    def decorator(func: Callable) -> Callable:
        @allure.description(description)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def allure_link(url: str, name: str = None):
    """
    Allure链接装饰器
    :param url: 链接URL
    :param name: 链接名称
    """
    def decorator(func: Callable) -> Callable:
        @allure.link(url, name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def allure_issue(issue_url: str, issue_name: str = None):
    """
    Allure问题装饰器
    :param issue_url: 问题URL
    :param issue_name: 问题名称
    """
    def decorator(func: Callable) -> Callable:
        @allure.issue(issue_url, issue_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def allure_testcase(testcase_url: str, testcase_name: str = None):
    """
    Allure测试用例装饰器
    :param testcase_url: 测试用例URL
    :param testcase_name: 测试用例名称
    """
    def decorator(func: Callable) -> Callable:
        @allure.testcase(testcase_url, testcase_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 便捷函数
def smoke_test(func: Callable) -> Callable:
    """冒烟测试装饰器"""
    return pytest.mark.smoke(func)


def regression_test(func: Callable) -> Callable:
    """回归测试装饰器"""
    return pytest.mark.regression(func)


def api_test_mark(func: Callable) -> Callable:
    """API测试标记装饰器"""
    return pytest.mark.api(func)


def ui_test_mark(func: Callable) -> Callable:
    """UI测试标记装饰器"""
    return pytest.mark.ui(func)


def unit_test_mark(func: Callable) -> Callable:
    """单元测试标记装饰器"""
    return pytest.mark.unit(func)


def integration_test_mark(func: Callable) -> Callable:
    """集成测试标记装饰器"""
    return pytest.mark.integration(func)


def slow_test_mark(func: Callable) -> Callable:
    """慢速测试标记装饰器"""
    return pytest.mark.slow(func)


def fast_test_mark(func: Callable) -> Callable:
    """快速测试标记装饰器"""
    return pytest.mark.fast(func)


def critical_test_mark(func: Callable) -> Callable:
    """关键测试标记装饰器"""
    return pytest.mark.critical(func)


def high_priority_test_mark(func: Callable) -> Callable:
    """高优先级测试标记装饰器"""
    return pytest.mark.high_priority(func)


def low_priority_test_mark(func: Callable) -> Callable:
    """低优先级测试标记装饰器"""
    return pytest.mark.low_priority(func) 