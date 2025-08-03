# coding: utf-8
# @Author: bgtech
"""
优化的conftest.py文件
整合了原有的conftest.py功能，并添加了更多实用的fixtures和hooks
"""

import pytest
import allure
import os
import sys
import time
import json
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# 导入项目模块
from common.config import get_config
from common.log import info, error, debug
from utils.http_utils import HTTPUtils
from utils.allure_utils import AllureUtils, attach_text, attach_json, attach_exception

# 导入ORM相关模块
from utils.orm_fixtures import *

# 导入数据驱动框架
from common.data_driven_framework import data_driven_framework, pytest_generate_tests


# ==================== 配置和初始化 ====================

def pytest_configure(config):
    """pytest配置钩子"""
    # 设置自定义标记
    config.addinivalue_line("markers", "slow: 标记为慢速测试")
    config.addinivalue_line("markers", "integration: 标记为集成测试")
    config.addinivalue_line("markers", "unit: 标记为单元测试")
    config.addinivalue_line("markers", "api: 标记为API测试")
    config.addinivalue_line("markers", "ui: 标记为UI测试")
    config.addinivalue_line("markers", "smoke: 标记为冒烟测试")
    config.addinivalue_line("markers", "regression: 标记为回归测试")

    # 确保report目录存在
    report_dir = Path("report")
    report_dir.mkdir(exist_ok=True)

    info("pytest配置完成")


def pytest_sessionstart(session):
    """测试会话开始时的钩子"""
    info("=" * 50)
    info("测试会话开始")
    info(f"Python版本: {sys.version}")
    info(f"pytest版本: {pytest.__version__}")
    info(f"工作目录: {os.getcwd()}")
    info("=" * 50)


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的钩子"""
    info("=" * 50)
    info("测试会话结束")
    info(f"退出状态: {exitstatus}")
    info("=" * 50)


# ==================== 核心Fixtures ====================

@pytest.fixture(scope="session")
def http_client():
    """全局HTTP客户端fixture"""
    from utils.http_utils import HTTPUtils

    # 从配置文件获取基础URL，提供默认值
    try:
        base_url = get_config('interface.base_url') or ''
    except:
        base_url = ''

    try:
        default_headers = get_config('interface.default_headers') or {}
    except:
        default_headers = {}

    try:
        timeout = get_config('interface.timeout') or 30
    except:
        timeout = 30

    client = HTTPUtils(
        base_url=base_url,
        default_headers=default_headers,
        timeout=timeout
    )

    info("HTTP客户端已初始化")
    yield client

    # 清理工作
    client.clear_session()
    info("HTTP客户端已清理")


@pytest.fixture(scope="session")
def allure_utils():
    """Allure工具类fixture"""
    return AllureUtils()


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    try:
        base_url = get_config('interface.base_url') or ''
    except:
        base_url = ''

    try:
        timeout = get_config('interface.timeout') or 30
    except:
        timeout = 30

    try:
        retry_times = get_config('interface.retry_times') or 3
    except:
        retry_times = 3

    try:
        log_level = get_config('log.level') or 'INFO'
    except:
        log_level = 'INFO'

    return {
        'base_url': base_url,
        'timeout': timeout,
        'retry_times': retry_times,
        'log_level': log_level
    }


# ==================== 测试数据Fixtures ====================

@pytest.fixture(scope="session")
def test_data():
    """测试数据fixture"""
    from common.get_caseparams import read_test_data

    def _load_test_data(file_path: str):
        """加载测试数据"""
        try:
            return read_test_data(file_path)
        except Exception as e:
            error(f"加载测试数据失败: {file_path}, 错误: {e}")
            return []

    return _load_test_data


@pytest.fixture(scope="session")
def db_connection():
    """数据库连接fixture"""
    from common.data_source import data_source_manager

    def _get_db_data(sql: str, db_type: str = None, env: str = 'test'):
        """获取数据库数据"""
        try:
            return data_source_manager.load_test_data_from_db(sql, db_type, env)
        except Exception as e:
            error(f"数据库查询失败: {sql}, 错误: {e}")
            return []

    yield _get_db_data

    # 清理数据库连接
    data_source_manager.close_all_connections()


# ==================== 环境相关Fixtures ====================

@pytest.fixture(scope="session")
def environment():
    """环境信息fixture"""
    env = os.getenv('TEST_ENV', 'test')

    try:
        base_url = get_config(f'interface.{env}.base_url') or ''
    except:
        base_url = ''

    try:
        timeout = get_config(f'interface.{env}.timeout') or 30
    except:
        timeout = 30

    try:
        headers = get_config(f'interface.{env}.headers') or {}
    except:
        headers = {}

    return {
        'name': env,
        'base_url': base_url,
        'timeout': timeout,
        'headers': headers
    }


@pytest.fixture(scope="session")
def test_environment():
    """测试环境设置fixture"""
    env = os.getenv('TEST_ENV', 'test')

    # 设置环境变量
    os.environ['TEST_ENV'] = env

    # 创建测试目录
    test_dirs = ['report', 'log', 'temp']
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)

    yield env

    # 清理临时文件
    temp_dir = Path('temp')
    if temp_dir.exists():
        for file in temp_dir.glob('*'):
            try:
                file.unlink()
            except:
                pass


# ==================== 日志和监控Fixtures ====================

@pytest.fixture(scope="function")
def test_logger():
    """测试日志fixture"""
    logger = logging.getLogger(f"test_{time.time()}")
    logger.setLevel(logging.DEBUG)

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


@pytest.fixture(scope="function")
def api_monitor():
    """API监控fixture"""
    from common.api_monitor import APIMonitor

    monitor = APIMonitor()
    yield monitor

    # 输出监控报告
    report = monitor.generate_report()
    if report:
        attach_text(str(report), "API监控报告")


# ==================== 断言和验证Fixtures ====================

@pytest.fixture(scope="function")
def assertion_utils():
    """断言工具fixture"""
    from common.assertion import AssertionUtils

    return AssertionUtils()


@pytest.fixture(scope="function")
def response_validator():
    """响应验证fixture"""

    def _validate_response(response, expected_status=200, expected_schema=None):
        """验证响应"""
        assert response.status_code == expected_status, \
            f"期望状态码 {expected_status}, 实际状态码 {response.status_code}"

        if expected_schema:
            # 这里可以添加JSON Schema验证
            pass

        return response

    return _validate_response


# ==================== 测试生命周期Fixtures ====================

@pytest.fixture(scope="function", autouse=True)
def test_setup_teardown(request):
    """测试设置和清理fixture"""
    test_name = request.node.name
    test_class = request.node.cls.__name__ if request.node.cls else "Unknown"

    # 测试开始
    info(f"开始测试: {test_class}.{test_name}")
    start_time = time.time()

    yield

    # 测试结束
    end_time = time.time()
    duration = end_time - start_time
    info(f"测试完成: {test_class}.{test_name}, 耗时: {duration:.2f}秒")


# ==================== Allure增强Hooks ====================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """捕获测试结果并附加到Allure"""
    outcome = yield
    rep = outcome.get_result()

    # 只在测试调用阶段处理
    if rep.when == "call":
        # 获取测试中的response对象（如果有）
        response = getattr(item, "response", None)
        if response and hasattr(response, "text"):
            try:
                allure.attach(
                    response.text,
                    name="response_failure",
                    attachment_type=allure.attachment_type.TEXT
                )
            except Exception as e:
                error(f"附加响应到Allure失败: {e}")

        # 获取测试数据（如果有）
        test_data = getattr(item, "test_data", None)
        if test_data:
            try:
                attach_json(test_data, "测试数据")
            except Exception as e:
                error(f"附加测试数据到Allure失败: {e}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    """测试设置时的钩子"""
    # 记录测试开始
    test_name = item.name
    test_class = item.cls.__name__ if item.cls else "Unknown"

    with allure.step(f"测试设置: {test_class}.{test_name}"):
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item):
    """测试清理时的钩子"""
    # 记录测试结束
    test_name = item.name
    test_class = item.cls.__name__ if item.cls else "Unknown"

    with allure.step(f"测试清理: {test_class}.{test_name}"):
        yield


# ==================== 错误处理Hooks ====================

def pytest_exception_interact(call, report):
    """异常处理钩子"""
    if report.failed:
        # 获取异常信息
        exc_info = call.excinfo
        if exc_info:
            error_msg = str(exc_info.value)
            traceback_info = str(exc_info.traceback)

            # 附加异常信息到Allure
            try:
                attach_exception(exc_info.value, "测试异常")
                attach_text(traceback_info, "异常堆栈")
            except Exception as e:
                error(f"附加异常信息到Allure失败: {e}")


# ==================== 性能监控Hooks ====================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """测试执行时的性能监控"""
    start_time = time.time()

    yield

    end_time = time.time()
    duration = end_time - start_time

    # 记录慢速测试
    if duration > 5.0:  # 超过5秒的测试
        test_name = item.name
        test_class = item.cls.__name__ if item.cls else "Unknown"
        info(f"慢速测试警告: {test_class}.{test_name} 耗时 {duration:.2f}秒")


# ==================== 报告生成Hooks ====================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """终端总结钩子"""
    # 统计测试结果
    stats = terminalreporter.stats
    passed = len(stats.get('passed', []))
    failed = len(stats.get('failed', []))
    skipped = len(stats.get('skipped', []))
    total = passed + failed + skipped

    info("=" * 50)
    info("测试执行总结:")
    info(f"总测试数: {total}")
    info(f"通过: {passed}")
    info(f"失败: {failed}")
    info(f"跳过: {skipped}")
    info(f"成功率: {(passed / total * 100):.1f}%" if total > 0 else "成功率: 0%")
    info("=" * 50)


# ==================== 工具函数 ====================

def get_test_data_path(filename: str) -> str:
    """获取测试数据文件路径"""
    data_dir = Path("caseparams")
    return str(data_dir / filename)


def create_test_report(test_name: str, data: Dict[str, Any]) -> str:
    """创建测试报告"""
    report_dir = Path("report")
    report_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"{test_name}_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return str(report_file)


# ==================== 便捷函数 ====================

def log_test_info(message: str):
    """记录测试信息"""
    info(f"[TEST_INFO] {message}")


def log_test_error(message: str, error: Exception = None):
    """记录测试错误"""
    if error:
        error(f"[TEST_ERROR] {message}: {error}")
    else:
        error(f"[TEST_ERROR] {message}")


def attach_test_data_to_allure(data: Dict[str, Any], name: str = "测试数据"):
    """将测试数据附加到Allure"""
    try:
        attach_json(data, name)
    except Exception as e:
        error(f"附加测试数据到Allure失败: {e}")


# ==================== 配置验证 ====================

def validate_test_config():
    """验证测试配置"""
    required_configs = [
        'interface.base_url',
        'interface.timeout',
        'log.level'
    ]

    missing_configs = []
    for config_key in required_configs:
        try:
            get_config(config_key)
        except:
            missing_configs.append(config_key)

    if missing_configs:
        warning_msg = f"缺少必要的配置项: {missing_configs}"
        error(warning_msg)
        return False

    return True


# 在会话开始时验证配置
@pytest.fixture(scope="session", autouse=True)
def config_validator():
    """配置验证fixture"""
    validate_test_config()
    yield 