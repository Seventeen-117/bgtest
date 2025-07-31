import pytest

# pytest会话级前置后置钩子

@pytest.fixture(scope='session', autouse=True)
def session_setup():
    """
    测试会话开始前后自动执行
    """
    print('测试会话开始')
    yield
    print('测试会话结束')

# 示例用法：
# pytest会自动调用，无需手动调用 