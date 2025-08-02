# coding: utf-8
# @Author: bgtech
"""
根目录conftest.py文件
导入utils/conftest.py中的所有fixtures和hooks
"""

# 导入utils/conftest.py中的所有内容
from utils.conftest import *

# 确保所有fixtures和hooks都可用
__all__ = [
    # Fixtures
    'http_client',
    'allure_utils', 
    'test_config',
    'test_data',
    'db_connection',
    'environment',
    'test_environment',
    'test_logger',
    'api_monitor',
    'assertion_utils',
    'response_validator',
    'test_setup_teardown',
    'config_validator',
    
    # Hooks
    'pytest_configure',
    'pytest_sessionstart',
    'pytest_sessionfinish',
    'pytest_runtest_makereport',
    'pytest_runtest_setup',
    'pytest_runtest_teardown',
    'pytest_runtest_call',
    'pytest_exception_interact',
    'pytest_terminal_summary',
    
    # Utility functions
    'get_test_data_path',
    'create_test_report',
    'log_test_info',
    'log_test_error',
    'attach_test_data_to_allure',
    'validate_test_config'
] 