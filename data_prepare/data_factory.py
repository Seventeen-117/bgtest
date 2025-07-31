# 数据造数脚本示例

def generate_test_user(user_id_prefix, count):
    """
    生成测试用户ID列表
    :param user_id_prefix: 用户ID前缀
    :param count: 生成数量
    :return: 用户ID列表
    """
    return [f"{user_id_prefix}{i:03d}" for i in range(1, count+1)]

# 示例用法：
# users = generate_test_user('testuser_', 5)
# print(users)  # ['testuser_001', 'testuser_002', ...] 