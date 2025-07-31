# coding: utf-8
# @Author: bgtech
import pytest
from common.get_caseparams import read_test_data
from common.data_source import get_test_data_from_db, get_redis_value, set_redis_value
from utils.http_utils import http_post
from common.log import info, error

class TestChatGatewayWithDynamicData:
    """使用动态数据源的聊天网关测试"""
    
    def test_chat_gateway_with_file_data(self):
        """使用文件数据的聊天网关测试"""
        # 从文件加载测试数据
        test_data = read_test_data('caseparams/test_chat_gateway.yaml')
        
        for case in test_data:
            self._execute_chat_test(case, "file")
    
    def test_chat_gateway_with_db_data(self):
        """使用数据库数据的聊天网关测试"""
        # 从数据库加载测试数据
        sql = """
        SELECT 
            'CHAT_' || id as case_id,
            '数据库测试用例 ' || id as description,
            'https://api.example.com/chat' as url,
            'POST' as method,
            JSON_OBJECT('user_id', user_id, 'message', message) as params,
            JSON_OBJECT('status_code', 200, 'success', true) as expected_result
        FROM chat_test_cases 
        WHERE status = 'active' 
        LIMIT 5
        """
        
        db_data = get_test_data_from_db(sql, 'mysql', 'test', 'chat_test_cases')
        
        if not db_data:
            pytest.skip("数据库中没有找到聊天测试数据")
        
        for case in db_data:
            self._execute_chat_test(case, "database")
    
    def test_chat_gateway_with_mixed_data(self):
        """使用混合数据源的聊天网关测试"""
        # 从文件加载基础配置
        file_data = read_test_data('caseparams/test_chat_gateway.yaml')
        
        # 从数据库加载用户数据
        user_sql = "SELECT user_id, username, email FROM users WHERE is_active = 1 LIMIT 3"
        user_data = get_test_data_from_db(user_sql, 'mysql', 'test', 'active_users')
        
        # 从Redis获取会话配置
        session_config = get_redis_value('chat:session:config', env='test')
        
        # 合并数据源
        for file_case in file_data:
            for user in user_data:
                # 创建混合测试用例
                mixed_case = file_case.copy()
                mixed_case.update({
                    'user_data': user,
                    'session_config': session_config,
                    'data_source': 'mixed'
                })
                
                self._execute_chat_test(mixed_case, "mixed")
    
    def test_chat_gateway_with_dynamic_params(self):
        """使用动态参数的聊天网关测试"""
        # 从Redis获取动态参数
        dynamic_params = get_redis_value('chat:dynamic:params', env='test')
        
        if not dynamic_params:
            # 设置默认参数
            default_params = {
                'user_id': 123,
                'message': 'Hello from dynamic test',
                'timestamp': '2024-01-01 12:00:00'
            }
            set_redis_value('chat:dynamic:params', str(default_params), env='test', expire=3600)
            dynamic_params = default_params
        else:
            import json
            dynamic_params = json.loads(dynamic_params)
        
        # 创建动态测试用例
        dynamic_case = {
            'case_id': 'CHAT_DYNAMIC_001',
            'description': '动态参数聊天测试',
            'url': 'https://api.example.com/chat',
            'method': 'POST',
            'params': dynamic_params,
            'expected_result': {
                'status_code': 200,
                'success': True
            },
            'data_source': 'dynamic'
        }
        
        self._execute_chat_test(dynamic_case, "dynamic")
    
    def test_chat_gateway_with_parameterized_db_data(self):
        """使用参数化数据库数据的聊天网关测试"""
        # 从数据库获取测试场景
        scenarios_sql = """
        SELECT 
            test_name,
            JSON_OBJECT('user_id', user_id, 'message', message, 'context', context) as input_data,
            JSON_OBJECT('status_code', expected_status, 'success', expected_success) as expected_result
        FROM chat_test_scenarios 
        WHERE category = 'api_test' AND status = 'active'
        """
        
        scenarios = get_test_data_from_db(scenarios_sql, 'mysql', 'test', 'chat_scenarios')
        
        if not scenarios:
            pytest.skip("数据库中没有找到聊天测试场景")
        
        # 参数化测试
        @pytest.mark.parametrize("scenario", scenarios)
        def test_chat_scenario(scenario):
            """使用数据库场景进行聊天测试"""
            test_name = scenario.get('test_name', 'Unknown Scenario')
            input_data = scenario.get('input_data', {})
            expected_result = scenario.get('expected_result', {})
            
            info(f"执行聊天测试场景: {test_name}")
            
            # 创建测试用例
            test_case = {
                'case_id': f'CHAT_SCENARIO_{test_name}',
                'description': f'场景测试: {test_name}',
                'url': 'https://api.example.com/chat',
                'method': 'POST',
                'params': input_data,
                'expected_result': expected_result,
                'data_source': 'parameterized_db'
            }
            
            self._execute_chat_test(test_case, "parameterized_db")
        
        # 执行所有场景
        for scenario in scenarios:
            test_chat_scenario(scenario)
    
    def test_chat_gateway_with_cache_strategy(self):
        """使用缓存策略的聊天网关测试"""
        # 使用缓存的数据源
        cached_sql = """
        SELECT 
            'CHAT_CACHE_' || id as case_id,
            '缓存测试用例 ' || id as description,
            'https://api.example.com/chat' as url,
            'POST' as method,
            JSON_OBJECT('user_id', user_id, 'message', message) as params,
            JSON_OBJECT('status_code', 200, 'success', true) as expected_result
        FROM chat_test_cases 
        WHERE category = 'cache_test'
        """
        
        # 使用缓存键
        cached_data = get_test_data_from_db(cached_sql, 'mysql', 'test', 'chat_cache_test')
        
        for case in cached_data:
            self._execute_chat_test(case, "cached")
    
    def _execute_chat_test(self, case, data_source_type):
        """执行聊天测试"""
        case_id = case.get('case_id', 'Unknown')
        description = case.get('description', 'No description')
        url = case.get('url')
        method = case.get('method', 'POST').upper()
        params = case.get('params', {})
        expected = case.get('expected_result', {})
        
        info(f"执行用例: {case_id} - {description} (数据源: {data_source_type})")
        info(f"请求地址: {url}")
        info(f"请求参数: {params}")
        
        try:
            if method == 'POST':
                resp = http_post(url, json_data=params)
            else:
                error(f"暂不支持的请求方式: {method}")
                pytest.skip("暂不支持的请求方式")
            
            info(f"接口返回: {resp}")
            
            # 断言
            for k, v in expected.items():
                assert resp.get(k) == v, f"断言失败: {k} 期望: {v} 实际: {resp.get(k)}"
            
            info(f"用例 {case_id} 执行成功")
            
        except Exception as e:
            error(f"用例 {case_id} 执行失败: {e}")
            raise
    
    def test_data_source_cleanup(self):
        """测试数据源清理"""
        from common.data_source import data_source_manager
        
        # 执行一些数据库操作
        sql = "SELECT COUNT(*) as count FROM chat_test_cases"
        result = get_test_data_from_db(sql, 'mysql', 'test')
        
        info(f"聊天测试用例总数: {result}")
        
        # 清理所有连接
        data_source_manager.close_all_connections()
        
        info("数据源连接已清理")

# 便捷函数
def load_chat_test_data(data_source_type: str = 'file'):
    """
    根据数据源类型加载聊天测试数据
    :param data_source_type: 数据源类型 (file, database, mixed, dynamic)
    """
    if data_source_type == 'file':
        return read_test_data('caseparams/test_chat_gateway.yaml')
    elif data_source_type == 'database':
        sql = "SELECT * FROM chat_test_cases WHERE status = 'active'"
        return get_test_data_from_db(sql, 'mysql', 'test', 'chat_cases')
    elif data_source_type == 'mixed':
        # 混合数据源
        file_data = read_test_data('caseparams/test_chat_gateway.yaml')
        db_data = get_test_data_from_db("SELECT * FROM chat_test_cases LIMIT 5", 'mysql', 'test')
        return file_data + db_data
    elif data_source_type == 'dynamic':
        # 动态数据源
        dynamic_config = get_redis_value('chat:test:config', env='test')
        if dynamic_config:
            import json
            return json.loads(dynamic_config)
        return []
    else:
        raise ValueError(f"不支持的数据源类型: {data_source_type}")

# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("聊天网关动态数据源测试")
    print("=" * 60)
    
    # 测试不同数据源
    data_sources = ['file', 'database', 'mixed', 'dynamic']
    
    for source_type in data_sources:
        try:
            print(f"\n测试 {source_type} 数据源:")
            data = load_chat_test_data(source_type)
            print(f"  加载了 {len(data)} 条聊天测试数据")
        except Exception as e:
            print(f"  {source_type} 数据源测试失败: {e}")
    
    print("\n✓ 聊天网关动态数据源测试完成！") 