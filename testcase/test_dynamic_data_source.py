# coding: utf-8
# @Author: bgtech
import pytest
from common.get_caseparams import read_test_data
from common.data_source import get_test_data_from_db, get_db_data, get_redis_value, set_redis_value
from common.log import info, error
from utils.http_utils import http_post

class TestDynamicDataSource:
    """动态数据源测试用例"""
    
    def test_data_from_file(self):
        """从文件加载测试数据"""
        # 从YAML文件加载数据
        test_data = read_test_data('caseparams/test_chat_gateway.yaml')
        info(f"从文件加载了 {len(test_data)} 条测试数据")
        
        # 验证数据格式
        for case in test_data:
            assert 'case_id' in case, "测试数据缺少case_id字段"
            assert 'url' in case, "测试数据缺少url字段"
            assert 'method' in case, "测试数据缺少method字段"
    
    def test_data_from_database(self):
        """从数据库加载测试数据"""
        # 示例SQL查询
        sql = "SELECT * FROM test_cases WHERE status = 'active' LIMIT 10"
        
        # 从数据库加载数据
        db_data = get_test_data_from_db(
            sql=sql,
            db_type='mysql',
            env='test',
            cache_key='active_test_cases'
        )
        
        info(f"从数据库加载了 {len(db_data)} 条测试数据")
        
        # 验证数据格式
        if db_data:
            for case in db_data:
                assert isinstance(case, dict), "数据库返回的数据应该是字典格式"
    
    def test_data_from_db_url_format(self):
        """使用db://格式从数据库加载数据"""
        # 使用db://格式的配置
        db_config = "db://mysql/test/SELECT * FROM test_cases WHERE status = 'active' LIMIT 5?cache_key=active_cases"
        
        # 从数据库加载数据
        test_data = read_test_data(db_config)
        
        info(f"使用db://格式从数据库加载了 {len(test_data)} 条测试数据")
        
        # 验证数据格式
        if test_data:
            for case in test_data:
                assert isinstance(case, dict), "数据库返回的数据应该是字典格式"
    
    def test_redis_data_source(self):
        """测试Redis数据源"""
        # 设置测试数据到Redis
        test_key = "test:user:123"
        test_value = {"user_id": 123, "username": "test_user", "email": "test@example.com"}
        
        success = set_redis_value(test_key, str(test_value), env='test', expire=300)
        assert success, "设置Redis数据失败"
        
        # 从Redis获取数据
        retrieved_value = get_redis_value(test_key, env='test')
        assert retrieved_value is not None, "从Redis获取数据失败"
        
        info(f"Redis数据源测试成功: {retrieved_value}")
    
    def test_mixed_data_sources(self):
        """测试混合数据源（文件+数据库）"""
        # 从文件加载基础配置
        file_data = read_test_data('caseparams/test_chat_gateway.yaml')
        
        # 从数据库加载动态数据
        sql = "SELECT * FROM user_profiles WHERE is_active = 1 LIMIT 3"
        db_data = get_test_data_from_db(sql, 'mysql', 'test', 'user_profiles')
        
        # 合并数据源
        combined_data = []
        
        # 为每个文件数据创建多个测试用例（基于数据库数据）
        for file_case in file_data:
            for db_case in db_data:
                # 合并文件数据和数据库数据
                combined_case = file_case.copy()
                combined_case.update(db_case)
                combined_case['data_source'] = 'mixed'
                combined_data.append(combined_case)
        
        info(f"混合数据源生成了 {len(combined_data)} 条测试用例")
        
        # 验证合并后的数据
        for case in combined_data:
            assert 'case_id' in case, "合并数据缺少case_id字段"
            assert 'data_source' in case, "合并数据缺少data_source字段"
            assert case['data_source'] == 'mixed', "data_source字段值不正确"
    
    def test_parameterized_test_with_db_data(self):
        """使用数据库数据进行参数化测试"""
        # 从数据库获取测试参数
        sql = "SELECT test_name, input_data, expected_result FROM test_scenarios WHERE category = 'api_test'"
        test_scenarios = get_test_data_from_db(sql, 'mysql', 'test', 'api_scenarios')
        
        if not test_scenarios:
            pytest.skip("数据库中没有找到测试场景数据")
        
        # 参数化测试
        @pytest.mark.parametrize("scenario", test_scenarios)
        def test_api_with_db_data(scenario):
            """使用数据库数据进行API测试"""
            test_name = scenario.get('test_name', 'Unknown Test')
            input_data = scenario.get('input_data', {})
            expected_result = scenario.get('expected_result', {})
            
            info(f"执行测试场景: {test_name}")
            info(f"输入数据: {input_data}")
            info(f"期望结果: {expected_result}")
            
            # 这里可以执行实际的API测试
            # 例如: response = http_post(url, json=input_data)
            # 然后进行断言
            
            # 示例断言
            assert 'test_name' in scenario, "测试场景缺少test_name字段"
            assert isinstance(input_data, dict), "input_data应该是字典格式"
            assert isinstance(expected_result, dict), "expected_result应该是字典格式"
            
            info(f"测试场景 {test_name} 执行完成")
        
        # 执行参数化测试
        for scenario in test_scenarios:
            test_api_with_db_data(scenario)
    
    def test_dynamic_sql_generation(self):
        """测试动态SQL生成"""
        # 从Redis获取查询条件
        condition_key = "test:query:condition"
        condition = get_redis_value(condition_key, env='test')
        
        if condition:
            # 动态生成SQL
            sql = f"SELECT * FROM test_data WHERE {condition} LIMIT 10"
        else:
            # 默认SQL
            sql = "SELECT * FROM test_data LIMIT 10"
        
        # 执行动态SQL查询
        dynamic_data = get_test_data_from_db(sql, 'mysql', 'test', 'dynamic_query')
        
        info(f"动态SQL查询返回 {len(dynamic_data)} 条数据")
        info(f"使用的SQL: {sql}")
        
        # 验证查询结果
        assert isinstance(dynamic_data, list), "查询结果应该是列表格式"
    
    def test_data_source_cleanup(self):
        """测试数据源清理"""
        from common.data_source import data_source_manager
        
        # 执行一些数据库操作
        sql = "SELECT COUNT(*) as count FROM test_data"
        result = get_db_data(sql, 'mysql', 'test')
        
        info(f"数据库查询结果: {result}")
        
        # 清理所有连接
        data_source_manager.close_all_connections()
        
        info("数据源连接已清理")

# 便捷函数示例
def load_test_data_by_type(data_type: str):
    """
    根据数据类型加载测试数据
    :param data_type: 数据类型 (file, database, redis, mixed)
    """
    if data_type == 'file':
        return read_test_data('caseparams/test_chat_gateway.yaml')
    elif data_type == 'database':
        sql = "SELECT * FROM test_cases WHERE status = 'active'"
        return get_test_data_from_db(sql, 'mysql', 'test', 'active_cases')
    elif data_type == 'redis':
        # 从Redis获取测试数据键列表
        test_keys = get_redis_value('test:data:keys', env='test')
        if test_keys:
            return [get_redis_value(key, env='test') for key in test_keys.split(',')]
        return []
    elif data_type == 'mixed':
        # 混合数据源
        file_data = read_test_data('caseparams/test_chat_gateway.yaml')
        db_data = get_test_data_from_db("SELECT * FROM test_cases LIMIT 5", 'mysql', 'test')
        return file_data + db_data
    else:
        raise ValueError(f"不支持的数据类型: {data_type}")

# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("动态数据源功能测试")
    print("=" * 60)
    
    # 测试不同数据源
    data_sources = ['file', 'database', 'redis', 'mixed']
    
    for source_type in data_sources:
        try:
            print(f"\n测试 {source_type} 数据源:")
            data = load_test_data_by_type(source_type)
            print(f"  加载了 {len(data)} 条数据")
        except Exception as e:
            print(f"  {source_type} 数据源测试失败: {e}")
    
    print("\n✓ 动态数据源功能测试完成！") 