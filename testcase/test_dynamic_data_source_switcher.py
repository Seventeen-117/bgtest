# coding: utf-8
# @Author: bgtech
"""
动态数据源切换测试用例
展示如何在测试用例中动态切换不同的数据源
"""

import pytest
import allure
from common.dynamic_data_source_switcher import (
    data_source_switcher, 
    switch_data_source, 
    with_data_source,
    get_current_data_source,
    get_data_from_current_source,
    execute_query_on_current_source
)
from common.log import info, error
from utils.http_utils import http_post, http_get


class TestDynamicDataSourceSwitcher:
    """动态数据源切换测试用例"""
    
    def test_switch_to_file_data_source(self):
        """测试切换到文件数据源"""
        # 切换到文件数据源
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        # 获取当前数据源配置
        current_config = get_current_data_source()
        assert current_config['type'] == 'file'
        assert 'test_chat_gateway.yaml' in current_config['path']
        
        # 从当前数据源获取数据
        data = get_data_from_current_source()
        assert len(data) > 0, "从文件数据源获取数据失败"
        
        info(f"成功从文件数据源获取 {len(data)} 条数据")
    
    def test_switch_to_database_data_source(self):
        """测试切换到数据库数据源"""
        # 切换到MySQL数据库数据源
        db_config = "db://mysql/test/SELECT * FROM test_cases WHERE status = 'active' LIMIT 5?cache_key=active_cases"
        success = data_source_switcher.switch_to(db_config)
        assert success, "切换到数据库数据源失败"
        
        # 获取当前数据源配置
        current_config = get_current_data_source()
        assert current_config['type'] == 'database'
        assert current_config['db_type'] == 'mysql'
        assert current_config['env'] == 'test'
        
        # 从当前数据源获取数据
        data = get_data_from_current_source()
        info(f"成功从数据库数据源获取 {len(data)} 条数据")
    
    def test_switch_to_redis_data_source(self):
        """测试切换到Redis数据源"""
        # 切换到Redis数据源
        redis_config = "redis://test/test:user:123"
        success = data_source_switcher.switch_to(redis_config)
        assert success, "切换到Redis数据源失败"
        
        # 获取当前数据源配置
        current_config = get_current_data_source()
        assert current_config['type'] == 'redis'
        assert current_config['env'] == 'test'
        
        # 从当前数据源获取数据
        data = get_data_from_current_source()
        info(f"成功从Redis数据源获取 {len(data)} 条数据")
    
    @switch_data_source("caseparams/test_chat_gateway.yaml")
    def test_with_decorator(self):
        """使用装饰器切换数据源"""
        # 获取当前数据源配置
        current_config = get_current_data_source()
        assert current_config['type'] == 'file'
        
        # 从当前数据源获取数据
        data = get_data_from_current_source()
        assert len(data) > 0, "使用装饰器获取数据失败"
        
        info(f"使用装饰器成功获取 {len(data)} 条数据")
    
    def test_with_context_manager(self):
        """使用上下文管理器临时切换数据源"""
        # 记录原始数据源
        original_config = get_current_data_source()
        
        # 使用上下文管理器临时切换到数据库数据源
        with with_data_source("db://mysql/test/SELECT * FROM test_cases LIMIT 3") as switcher:
            # 在上下文中获取数据
            data = get_data_from_current_source()
            info(f"在上下文中获取到 {len(data)} 条数据")
            
            # 验证当前数据源
            current_config = get_current_data_source()
            assert current_config['type'] == 'database'
        
        # 验证数据源已恢复
        restored_config = get_current_data_source()
        if original_config:
            assert restored_config == original_config, "数据源未正确恢复"
        
        info("上下文管理器测试完成")
    
    def test_execute_query_on_current_source(self):
        """测试在当前数据源上执行查询"""
        # 切换到数据库数据源
        success = data_source_switcher.switch_to("db://mysql/test/SELECT 1 as test")
        assert success, "切换到数据库数据源失败"
        
        # 执行查询
        result = execute_query_on_current_source("SELECT COUNT(*) as count FROM test_cases")
        assert len(result) > 0, "执行查询失败"
        
        info(f"查询结果: {result}")
    
    def test_multiple_data_source_switching(self):
        """测试多次数据源切换"""
        # 切换到文件数据源
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        file_data = get_data_from_current_source()
        info(f"从文件数据源获取 {len(file_data)} 条数据")
        
        # 切换到数据库数据源
        success = data_source_switcher.switch_to("db://mysql/test/SELECT * FROM test_cases LIMIT 3")
        assert success, "切换到数据库数据源失败"
        
        db_data = get_data_from_current_source()
        info(f"从数据库数据源获取 {len(db_data)} 条数据")
        
        # 切换到Redis数据源
        success = data_source_switcher.switch_to("redis://test/test:config")
        assert success, "切换到Redis数据源失败"
        
        redis_data = get_data_from_current_source()
        info(f"从Redis数据源获取 {len(redis_data)} 条数据")
        
        # 查看切换历史
        history = data_source_switcher.get_switch_history()
        assert len(history) >= 3, "切换历史记录不完整"
        
        info(f"数据源切换历史: {len(history)} 次切换")
    
    def test_data_source_with_api_test(self):
        """结合API测试的数据源切换"""
        # 切换到文件数据源获取测试用例
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        test_cases = get_data_from_current_source()
        
        for i, test_case in enumerate(test_cases[:3]):  # 只测试前3个用例
            with allure.step(f"测试用例 {i+1}: {test_case.get('case_id', 'unknown')}"):
                # 获取测试数据
                url = test_case.get('url')
                method = test_case.get('method', 'GET')
                params = test_case.get('params', {})
                
                # 执行API请求
                if method.upper() == 'POST':
                    response = http_post(url, json=params)
                else:
                    response = http_get(url, params=params)
                
                # 验证响应
                assert response is not None, f"API请求失败: {url}"
                info(f"API测试成功: {url} - 状态码: {response.get('status_code', 'unknown')}")
    
    def test_dynamic_sql_generation(self):
        """测试动态SQL生成"""
        # 切换到数据库数据源
        success = data_source_switcher.switch_to("db://mysql/test/SELECT * FROM test_cases")
        assert success, "切换到数据库数据源失败"
        
        # 动态生成SQL查询
        test_conditions = [
            "WHERE status = 'active'",
            "WHERE priority = 'high'",
            "WHERE category = 'api_test'"
        ]
        
        for condition in test_conditions:
            sql = f"SELECT * FROM test_cases {condition} LIMIT 5"
            result = execute_query_on_current_source(sql)
            info(f"动态SQL查询 '{condition}' 返回 {len(result)} 条结果")
    
    def test_cache_management(self):
        """测试缓存管理"""
        # 切换到数据库数据源并启用缓存
        db_config = "db://mysql/test/SELECT * FROM test_cases LIMIT 5?cache_key=test_cache"
        success = data_source_switcher.switch_to(db_config)
        assert success, "切换到数据库数据源失败"
        
        # 第一次获取数据（会缓存）
        data1 = get_data_from_current_source()
        info(f"第一次获取数据: {len(data1)} 条")
        
        # 第二次获取数据（从缓存）
        data2 = get_data_from_current_source()
        info(f"第二次获取数据: {len(data2)} 条")
        
        # 清除缓存
        data_source_switcher.clear_cache("test_cache")
        info("缓存已清除")
        
        # 再次获取数据（重新查询）
        data3 = get_data_from_current_source()
        info(f"清除缓存后获取数据: {len(data3)} 条")
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效的数据源配置
        success = data_source_switcher.switch_to("invalid://config")
        assert not success, "应该拒绝无效的数据源配置"
        
        # 测试不存在的文件
        success = data_source_switcher.switch_to("caseparams/non_existent_file.yaml")
        assert not success, "应该拒绝不存在的文件"
        
        # 测试无效的数据库配置
        success = data_source_switcher.switch_to("db://invalid_db/test/SELECT * FROM test_cases")
        assert not success, "应该拒绝无效的数据库配置"
        
        info("错误处理测试完成")


class TestDataSourceSwitcherIntegration:
    """数据源切换器集成测试"""
    
    def test_integration_with_existing_framework(self):
        """测试与现有框架的集成"""
        from common.data_driven_framework import DataDrivenFramework
        from common.data_source import get_test_data_from_db
        
        # 创建数据驱动框架实例
        framework = DataDrivenFramework()
        
        # 使用数据源切换器
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        # 从切换器获取数据
        switcher_data = get_data_from_current_source()
        
        # 从框架获取数据
        framework_data = framework.load_test_data("caseparams/test_chat_gateway.yaml", "file")
        
        # 验证数据一致性
        assert len(switcher_data) == len(framework_data), "数据源切换器与框架数据不一致"
        
        info("数据源切换器与现有框架集成测试成功")
    
    def test_performance_comparison(self):
        """性能对比测试"""
        import time
        
        # 测试数据源切换器的性能
        start_time = time.time()
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        switcher_data = get_data_from_current_source()
        switcher_time = time.time() - start_time
        
        # 测试传统方式的性能
        start_time = time.time()
        from common.get_caseparams import read_test_data
        traditional_data = read_test_data("caseparams/test_chat_gateway.yaml")
        traditional_time = time.time() - start_time
        
        info(f"数据源切换器耗时: {switcher_time:.4f}秒")
        info(f"传统方式耗时: {traditional_time:.4f}秒")
        info(f"性能差异: {abs(switcher_time - traditional_time):.4f}秒")
        
        # 验证数据一致性
        assert len(switcher_data) == len(traditional_data), "数据不一致"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 