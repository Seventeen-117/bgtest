"""
Allure装饰器模块
提供各种Allure装饰器，避免与pytest的fixture检测冲突
"""

import time
import allure
from functools import wraps
from typing import Dict, Any
from .allure_utils import AllureUtils


def allure_test_case(title: str, description: str = ""):
    """测试用例装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with allure.step(f"测试用例: {title}"):
                if description:
                    allure.description(description)
                
                # 记录开始时间
                start_time = time.time()
                
                try:
                    # 执行测试函数
                    result = func(*args, **kwargs)
                    
                    # 记录执行时间
                    execution_time = time.time() - start_time
                    allure.attach(
                        f"执行时间: {execution_time:.2f}秒",
                        "执行时间",
                        allure.attachment_type.TEXT
                    )
                    
                    return result
                except Exception as e:
                    # 记录异常
                    AllureUtils.attach_exception(e, f"测试用例异常: {title}")
                    raise
        return wrapper
    return decorator

# 使用 allure_test_case 而不是 test_case 来避免 pytest 检测
# test_case = allure_test_case  # 已注释，避免 pytest 检测冲突


def allure_api_test(api_name: str, method: str, url: str):
    """API测试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with allure.step(f"API测试: {api_name}"):
                allure.attach(f"API: {api_name}\n方法: {method}\nURL: {url}", "API信息", allure.attachment_type.TEXT)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    AllureUtils.attach_exception(e, f"API测试异常: {api_name}")
                    raise
        return wrapper
    return decorator


def allure_data_driven_test(data_source: str, data_type: str = "file"):
    """数据驱动测试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with allure.step(f"数据驱动测试: {data_source}"):
                allure.attach(f"数据源: {data_source}\n数据类型: {data_type}", "数据驱动信息", allure.attachment_type.TEXT)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    AllureUtils.attach_exception(e, f"数据驱动测试异常: {data_source}")
                    raise
        return wrapper
    return decorator

# 使用 allure_* 前缀来避免 pytest 检测
# api_test = allure_api_test  # 已注释，避免 pytest 检测冲突
# data_driven_test = allure_data_driven_test  # 已注释，避免 pytest 检测冲突


def performance_test(threshold_ms: float = 1000.0):
    """性能测试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with allure.step(f"性能测试: {func.__name__}"):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    execution_time = (time.time() - start_time) * 1000
                    allure.attach(
                        f"执行时间: {execution_time:.2f}ms\n阈值: {threshold_ms}ms",
                        "性能测试结果",
                        allure.attachment_type.TEXT
                    )
                    
                    if execution_time > threshold_ms:
                        allure.attach(
                            f"性能警告: 执行时间 {execution_time:.2f}ms 超过阈值 {threshold_ms}ms",
                            "性能警告",
                            allure.attachment_type.TEXT
                        )
                    
                    return result
                except Exception as e:
                    AllureUtils.attach_exception(e, f"性能测试异常: {func.__name__}")
                    raise
        return wrapper
    return decorator


def security_test(security_level: str = "medium"):
    """安全测试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with allure.step(f"安全测试: {func.__name__}"):
                allure.attach(f"安全级别: {security_level}", "安全测试信息", allure.attachment_type.TEXT)
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    AllureUtils.attach_exception(e, f"安全测试异常: {func.__name__}")
                    raise
        return wrapper
    return decorator 