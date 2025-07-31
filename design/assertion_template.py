# 常用断言函数模板

def assert_equal(actual, expected, msg=None):
    """
    断言实际值等于期望值
    :param actual: 实际值
    :param expected: 期望值
    :param msg: 失败时的自定义提示
    """
    assert actual == expected, msg or f"期望: {expected}, 实际: {actual}"

def assert_in(item, container, msg=None):
    """
    断言item在container中
    :param item: 元素
    :param container: 容器
    :param msg: 失败时的自定义提示
    """
    assert item in container, msg or f"{item} 不在 {container} 中"

# 示例用法：
# assert_equal(1, 1)
# assert_in('a', 'abc') 