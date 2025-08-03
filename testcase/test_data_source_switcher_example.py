# coding: utf-8
# @Author: bgtech
"""
动态数据源切换使用示例
展示如何在现有测试用例中集成动态数据源切换功能
"""

import pytest
import allure
from common.dynamic_data_source_switcher import (
    data_source_switcher, 
    switch_data_source, 
    with_data_source,
    get_data_from_current_source
)
from common.log import info
from utils.http_utils import http_post, http_get


class TestDataSourceSwitcherExample:
    """动态数据源切换使用示例"""
    
    def test_basic_usage_example(self):
        """基础使用示例"""
        # 示例1: 从文件数据源获取测试用例
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        test_cases = get_data_from_current_source()
        info(f"从文件获取到 {len(test_cases)} 个测试用例")
        
        # 示例2: 切换到数据库数据源获取用户数据
        success = data_source_switcher.switch_to("db://mysql/test/SELECT user_id, username FROM users WHERE is_active = 1 LIMIT 5")
        assert success, "切换到数据库数据源失败"
        
        user_data = get_data_from_current_source()
        info(f"从数据库获取到 {len(user_data)} 个用户")
        
        # 示例3: 切换到Redis数据源获取配置
        success = data_source_switcher.switch_to("redis://test/test:api_config")
        assert success, "切换到Redis数据源失败"
        
        config_data = get_data_from_current_source()
        info(f"从Redis获取到配置数据: {config_data}")
    
    @switch_data_source("caseparams/test_chat_gateway.yaml")
    def test_with_decorator_example(self):
        """使用装饰器的示例"""
        # 获取测试用例
        test_cases = get_data_from_current_source()
        
        # 执行前3个测试用例
        for i, test_case in enumerate(test_cases[:3]):
            with allure.step(f"执行测试用例 {i+1}"):
                case_id = test_case.get('case_id', f'case_{i}')
                url = test_case.get('url')
                method = test_case.get('method', 'GET')
                params = test_case.get('params', {})
                
                info(f"执行测试用例: {case_id}")
                info(f"请求URL: {url}")
                info(f"请求方法: {method}")
                info(f"请求参数: {params}")
                
                # 这里可以添加实际的API调用逻辑
                # response = http_post(url, json=params) if method.upper() == 'POST' else http_get(url, params=params)
    
    def test_context_manager_example(self):
        """使用上下文管理器的示例"""
        # 记录原始数据源
        original_data = get_data_from_current_source()
        
        # 临时切换到数据库数据源
        with with_data_source("db://mysql/test/SELECT * FROM test_cases LIMIT 3") as switcher:
            db_data = get_data_from_current_source()
            info(f"临时从数据库获取到 {len(db_data)} 条数据")
            
            # 在上下文中执行一些操作
            for record in db_data:
                info(f"处理数据记录: {record}")
        
        # 验证数据源已恢复
        restored_data = get_data_from_current_source()
        if original_data:
            assert restored_data == original_data, "数据源未正确恢复"
        
        info("上下文管理器示例完成")
    
    def test_multi_environment_example(self):
        """多环境测试示例"""
        environments = ['dev', 'test']  # 可以根据需要添加 'prod'
        
        for env in environments:
            with allure.step(f"测试环境: {env}"):
                # 切换到对应环境的数据源
                db_config = f"db://mysql/{env}/SELECT * FROM test_cases WHERE env = '{env}' LIMIT 5"
                success = data_source_switcher.switch_to(db_config)
                
                if success:
                    env_data = get_data_from_current_source()
                    info(f"环境 {env} 获取到 {len(env_data)} 条测试用例")
                    
                    # 为每个环境的测试用例执行测试
                    for test_case in env_data:
                        case_id = test_case.get('case_id', 'unknown')
                        info(f"在环境 {env} 中执行测试用例: {case_id}")
                        
                        # 这里可以添加环境特定的测试逻辑
                        # 例如：使用不同环境的API地址
                        # api_url = f"https://{env}-api.example.com/test"
                else:
                    info(f"环境 {env} 数据源不可用，跳过测试")
    
    def test_data_combination_example(self):
        """数据源组合示例"""
        # 从文件获取基础测试配置
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        base_configs = get_data_from_current_source()
        info(f"获取到 {len(base_configs)} 个基础测试配置")
        
        # 从数据库获取动态测试数据
        success = data_source_switcher.switch_to("db://mysql/test/SELECT user_id, username, email FROM users WHERE is_active = 1 LIMIT 3")
        assert success, "切换到数据库数据源失败"
        
        dynamic_data = get_data_from_current_source()
        info(f"获取到 {len(dynamic_data)} 条动态测试数据")
        
        # 组合数据源生成测试用例
        combined_test_cases = []
        for base_config in base_configs:
            for dynamic_record in dynamic_data:
                # 合并基础配置和动态数据
                combined_case = base_config.copy()
                combined_case.update({
                    'user_data': dynamic_record,
                    'data_source': 'combined',
                    'combined_id': f"{base_config.get('case_id', 'base')}_{dynamic_record.get('user_id', 'user')}"
                })
                combined_test_cases.append(combined_case)
        
        info(f"生成了 {len(combined_test_cases)} 个组合测试用例")
        
        # 执行组合测试用例
        for i, test_case in enumerate(combined_test_cases[:5]):  # 只执行前5个
            with allure.step(f"执行组合测试用例 {i+1}"):
                case_id = test_case.get('combined_id', f'combined_{i}')
                user_data = test_case.get('user_data', {})
                
                info(f"执行组合测试用例: {case_id}")
                info(f"用户数据: {user_data}")
                
                # 这里可以添加实际的测试逻辑
                # 例如：使用用户数据调用API
                # response = http_post(test_case['url'], json=user_data)
    
    def test_cache_example(self):
        """缓存使用示例"""
        # 使用缓存的数据源配置
        cached_config = "db://mysql/test/SELECT * FROM test_cases WHERE status = 'active'?cache_key=active_cases"
        success = data_source_switcher.switch_to(cached_config)
        assert success, "切换到缓存数据源失败"
        
        # 第一次获取数据（会缓存）
        import time
        start_time = time.time()
        data1 = get_data_from_current_source()
        first_time = time.time() - start_time
        
        # 第二次获取数据（从缓存）
        start_time = time.time()
        data2 = get_data_from_current_source()
        second_time = time.time() - start_time
        
        info(f"首次获取耗时: {first_time:.4f}秒")
        info(f"缓存获取耗时: {second_time:.4f}秒")
        
        if first_time > 0:
            improvement = ((first_time - second_time) / first_time * 100)
            info(f"性能提升: {improvement:.2f}%")
        
        # 清除缓存
        data_source_switcher.clear_cache("active_cases")
        info("缓存已清除")
    
    def test_error_handling_example(self):
        """错误处理示例"""
        # 尝试切换到无效的数据源
        success = data_source_switcher.switch_to("invalid://data/source")
        assert not success, "应该拒绝无效的数据源配置"
        
        # 尝试切换到不存在的文件
        success = data_source_switcher.switch_to("caseparams/non_existent_file.yaml")
        assert not success, "应该拒绝不存在的文件"
        
        # 尝试切换到无效的数据库配置
        success = data_source_switcher.switch_to("db://invalid_db/test/SELECT * FROM test_cases")
        assert not success, "应该拒绝无效的数据库配置"
        
        # 回退到有效的文件数据源
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "回退到文件数据源失败"
        
        data = get_data_from_current_source()
        info(f"使用回退数据源获取到 {len(data)} 条数据")
    
    def test_switch_history_example(self):
        """切换历史记录示例"""
        # 执行多次数据源切换
        data_sources = [
            "caseparams/test_chat_gateway.yaml",
            "db://mysql/test/SELECT * FROM test_cases LIMIT 3",
            "redis://test/test:config"
        ]
        
        for i, data_source in enumerate(data_sources):
            success = data_source_switcher.switch_to(data_source)
            if success:
                data = get_data_from_current_source()
                info(f"切换 {i+1}: 从 {data_source} 获取到 {len(data)} 条数据")
            else:
                info(f"切换 {i+1}: {data_source} 失败")
        
        # 查看切换历史
        history = data_source_switcher.get_switch_history()
        info(f"数据源切换历史记录: {len(history)} 次切换")
        
        for i, record in enumerate(history[-3:]):  # 显示最近3次切换
            config = record['config']
            timestamp = record['timestamp']
            info(f"历史记录 {i+1}: {timestamp} - {config.get('name', 'unknown')}")


class TestDataSourceSwitcherIntegration:
    """数据源切换器集成示例"""
    
    def test_integration_with_existing_framework(self):
        """与现有框架集成的示例"""
        from common.data_driven_framework import DataDrivenFramework
        from common.get_caseparams import read_test_data
        
        # 使用数据源切换器
        success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        switcher_data = get_data_from_current_source()
        
        # 使用现有框架
        framework = DataDrivenFramework()
        framework_data = framework.load_test_data("caseparams/test_chat_gateway.yaml", "file")
        
        # 使用传统方式
        traditional_data = read_test_data("caseparams/test_chat_gateway.yaml")
        
        # 验证数据一致性
        assert len(switcher_data) == len(framework_data), "数据源切换器与框架数据不一致"
        assert len(switcher_data) == len(traditional_data), "数据源切换器与传统方式数据不一致"
        
        info("数据源切换器与现有框架集成测试成功")
    
    def test_performance_comparison(self):
        """性能对比示例"""
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
        
        if traditional_time > 0:
            performance_diff = abs(switcher_time - traditional_time)
            info(f"性能差异: {performance_diff:.4f}秒")
        
        # 验证数据一致性
        assert len(switcher_data) == len(traditional_data), "数据不一致"


if __name__ == "__main__":
    # 运行示例测试
    pytest.main([__file__, "-v", "-s"]) 