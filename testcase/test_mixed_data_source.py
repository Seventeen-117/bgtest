# coding: utf-8
# @Author: bgtech
"""
混合数据源测试用例
测试文件数据 + 数据库数据的组合逻辑
"""

import pytest
import json
from common.dynamic_data_source_switcher import data_source_switcher
from common.enhanced_data_source_switcher import enhanced_data_source_switcher
from common.data_source import set_redis_value
from common.log import info, error


class TestMixedDataSource:
    """混合数据源测试用例"""
    
    def test_mixed_data_source_basic(self):
        """测试基础混合数据源功能"""
        # 配置混合数据源
        mixed_config = {
            'type': 'mixed',
            'name': 'mixed_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as test_id, "test_user" as username',
            'merge_strategy': 'cross_product',
            'cache_config_key': 'test:cache:config'
        }
        
        # 切换到混合数据源
        success = data_source_switcher.switch_to(mixed_config)
        assert success, "切换到混合数据源失败"
        
        # 获取混合数据
        data = data_source_switcher.get_data()
        assert len(data) > 0, "混合数据源获取数据失败"
        
        # 验证数据格式
        for case in data:
            assert 'data_source' in case, "混合数据缺少data_source字段"
            assert case['data_source'] == 'mixed', "data_source字段值不正确"
            assert 'merge_strategy' in case, "混合数据缺少merge_strategy字段"
        
        info(f"基础混合数据源测试通过，获取到 {len(data)} 条数据")
    
    def test_mixed_data_source_cross_product(self):
        """测试笛卡尔积合并策略"""
        # 配置混合数据源
        mixed_config = {
            'type': 'mixed',
            'name': 'cross_product_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username UNION SELECT 2, "user2"',
            'merge_strategy': 'cross_product'
        }
        
        # 切换到混合数据源
        success = data_source_switcher.switch_to(mixed_config)
        assert success, "切换到混合数据源失败"
        
        # 获取混合数据
        data = data_source_switcher.get_data()
        
        # 验证笛卡尔积合并结果
        # 基础数据有3条，动态数据有2条，应该生成3*2=6条数据
        assert len(data) >= 6, f"笛卡尔积合并结果不正确，期望至少6条，实际{len(data)}条"
        
        # 验证每条数据都包含基础数据和动态数据的字段
        for case in data:
            assert 'case_id' in case, "合并数据缺少基础数据字段case_id"
            assert 'user_id' in case, "合并数据缺少动态数据字段user_id"
            assert 'username' in case, "合并数据缺少动态数据字段username"
        
        info(f"笛卡尔积合并测试通过，生成 {len(data)} 条数据")
    
    def test_mixed_data_source_append(self):
        """测试追加合并策略"""
        # 配置混合数据源
        mixed_config = {
            'type': 'mixed',
            'name': 'append_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username',
            'merge_strategy': 'append'
        }
        
        # 切换到混合数据源
        success = data_source_switcher.switch_to(mixed_config)
        assert success, "切换到混合数据源失败"
        
        # 获取混合数据
        data = data_source_switcher.get_data()
        
        # 验证追加合并结果
        # 基础数据有3条，动态数据有1条，应该生成3+1=4条数据
        assert len(data) >= 4, f"追加合并结果不正确，期望至少4条，实际{len(data)}条"
        
        # 验证前3条是基础数据
        for i in range(min(3, len(data))):
            assert 'case_id' in data[i], f"第{i+1}条数据缺少基础数据字段case_id"
            assert data[i]['merge_strategy'] == 'append', f"第{i+1}条数据merge_strategy不正确"
        
        info(f"追加合并测试通过，生成 {len(data)} 条数据")
    
    def test_mixed_data_source_override(self):
        """测试覆盖合并策略"""
        # 配置混合数据源
        mixed_config = {
            'type': 'mixed',
            'name': 'override_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username UNION SELECT 2, "user2"',
            'merge_strategy': 'override'
        }
        
        # 切换到混合数据源
        success = data_source_switcher.switch_to(mixed_config)
        assert success, "切换到混合数据源失败"
        
        # 获取混合数据
        data = data_source_switcher.get_data()
        
        # 验证覆盖合并结果
        assert len(data) > 0, "覆盖合并结果为空"
        
        # 验证覆盖逻辑
        for i, case in enumerate(data):
            assert 'case_id' in case, f"第{i+1}条数据缺少基础数据字段case_id"
            assert case['merge_strategy'] == 'override', f"第{i+1}条数据merge_strategy不正确"
            
            # 如果有对应的动态数据，应该包含动态数据字段
            if i < 2:  # 假设动态数据有2条
                assert 'user_id' in case, f"第{i+1}条数据缺少动态数据字段user_id"
                assert 'username' in case, f"第{i+1}条数据缺少动态数据字段username"
        
        info(f"覆盖合并测试通过，生成 {len(data)} 条数据")
    
    def test_mixed_data_source_with_redis_cache(self):
        """测试带Redis缓存的混合数据源"""
        # 设置Redis缓存配置
        cache_config = {
            'timeout': 30,
            'retry_count': 3,
            'headers': {
                'Content-Type': 'application/json',
                'User-Agent': 'MixedDataSourceTest/1.0'
            }
        }
        
        # 将缓存配置存储到Redis
        cache_key = 'test:cache:config'
        set_redis_value(cache_key, json.dumps(cache_config), env='test')
        
        # 配置混合数据源
        mixed_config = {
            'type': 'mixed',
            'name': 'redis_cache_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username',
            'merge_strategy': 'cross_product',
            'cache_config_key': cache_key,
            'env': 'test'
        }
        
        # 切换到混合数据源
        success = data_source_switcher.switch_to(mixed_config)
        assert success, "切换到混合数据源失败"
        
        # 获取混合数据
        data = data_source_switcher.get_data()
        assert len(data) > 0, "带Redis缓存的混合数据源获取数据失败"
        
        # 验证缓存配置被正确合并
        for case in data:
            assert 'timeout' in case, "缓存配置timeout字段缺失"
            assert 'retry_count' in case, "缓存配置retry_count字段缺失"
            assert 'headers' in case, "缓存配置headers字段缺失"
            assert case['timeout'] == 30, "缓存配置timeout值不正确"
            assert case['retry_count'] == 3, "缓存配置retry_count值不正确"
        
        info(f"带Redis缓存的混合数据源测试通过，生成 {len(data)} 条数据")
    
    def test_mixed_data_source_enhanced(self):
        """测试增强版混合数据源功能"""
        # 配置混合数据源
        mixed_config = {
            'type': 'mixed',
            'name': 'enhanced_mixed_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username UNION SELECT 2, "user2"',
            'merge_strategy': 'cross_product',
            'cache_config_key': 'test:cache:config'
        }
        
        # 使用增强版数据源切换器
        success = enhanced_data_source_switcher.switch_to(mixed_config)
        assert success, "增强版切换到混合数据源失败"
        
        # 获取混合数据
        data = enhanced_data_source_switcher.get_data()
        assert len(data) > 0, "增强版混合数据源获取数据失败"
        
        # 验证数据格式
        for case in data:
            assert 'data_source' in case, "增强版混合数据缺少data_source字段"
            assert case['data_source'] == 'mixed', "增强版混合数据data_source字段值不正确"
            assert 'merge_strategy' in case, "增强版混合数据缺少merge_strategy字段"
        
        # 获取性能指标
        metrics = enhanced_data_source_switcher.get_metrics()
        assert metrics['switch_count'] > 0, "增强版性能指标收集失败"
        
        info(f"增强版混合数据源测试通过，获取到 {len(data)} 条数据，指标: {metrics}")
    
    def test_mixed_data_source_error_handling(self):
        """测试混合数据源错误处理"""
        # 配置无效的混合数据源
        invalid_config = {
            'type': 'mixed',
            'name': 'invalid_test',
            'base_config': 'caseparams/nonexistent_file.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT * FROM nonexistent_table',
            'merge_strategy': 'cross_product'
        }
        
        # 切换到无效的混合数据源
        success = data_source_switcher.switch_to(invalid_config)
        # 应该失败，因为文件不存在
        assert not success, "无效的混合数据源应该切换失败"
        
        # 测试部分有效的情况
        partial_valid_config = {
            'type': 'mixed',
            'name': 'partial_valid_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',  # 有效文件
            'dynamic_data_query': 'db://mysql/test/SELECT * FROM nonexistent_table',  # 无效查询
            'merge_strategy': 'cross_product'
        }
        
        # 切换到部分有效的混合数据源
        success = data_source_switcher.switch_to(partial_valid_config)
        # 应该成功，因为基础数据有效
        assert success, "部分有效的混合数据源应该切换成功"
        
        # 获取数据
        data = data_source_switcher.get_data()
        # 应该只有基础数据
        assert len(data) > 0, "部分有效的混合数据源应该返回基础数据"
        
        info(f"混合数据源错误处理测试通过，部分有效配置返回 {len(data)} 条数据")
    
    def test_mixed_data_source_performance(self):
        """测试混合数据源性能"""
        import time
        
        # 配置混合数据源
        mixed_config = {
            'type': 'mixed',
            'name': 'performance_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username UNION SELECT 2, "user2" UNION SELECT 3, "user3"',
            'merge_strategy': 'cross_product'
        }
        
        # 测试原始数据源切换器性能
        start_time = time.time()
        success = data_source_switcher.switch_to(mixed_config)
        data1 = data_source_switcher.get_data()
        original_time = time.time() - start_time
        
        # 测试增强版数据源切换器性能
        start_time = time.time()
        success = enhanced_data_source_switcher.switch_to(mixed_config)
        data2 = enhanced_data_source_switcher.get_data()
        enhanced_time = time.time() - start_time
        
        # 验证数据一致性
        assert len(data1) == len(data2), "原始版本和增强版数据量不一致"
        
        # 验证性能
        assert original_time < 5.0, f"原始版本性能过慢: {original_time:.4f}s"
        assert enhanced_time < 5.0, f"增强版性能过慢: {enhanced_time:.4f}s"
        
        info(f"混合数据源性能测试通过: 原始版本 {original_time:.4f}s, 增强版 {enhanced_time:.4f}s, 数据量 {len(data1)} 条")


class TestMixedDataSourceAdvanced:
    """高级混合数据源测试用例"""
    
    def test_mixed_data_source_with_complex_config(self):
        """测试复杂配置的混合数据源"""
        # 复杂的混合数据源配置
        complex_config = {
            'type': 'mixed',
            'name': 'complex_mixed_test',
            'base_config': {
                'file_path': 'caseparams/test_chat_gateway.yaml',
                'description': '复杂混合数据源测试',
                'priority': 'high'
            },
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username, "active" as status UNION SELECT 2, "user2", "inactive"',
            'merge_strategy': 'cross_product',
            'cache_config_key': 'test:cache:complex_config',
            'env': 'test'
        }
        
        # 切换到复杂混合数据源
        success = data_source_switcher.switch_to(complex_config)
        assert success, "切换到复杂混合数据源失败"
        
        # 获取混合数据
        data = data_source_switcher.get_data()
        assert len(data) > 0, "复杂混合数据源获取数据失败"
        
        # 验证复杂配置被正确处理
        for case in data:
            assert 'description' in case, "复杂配置description字段缺失"
            assert 'priority' in case, "复杂配置priority字段缺失"
            assert 'user_id' in case, "动态数据user_id字段缺失"
            assert 'username' in case, "动态数据username字段缺失"
            assert 'status' in case, "动态数据status字段缺失"
            assert case['description'] == '复杂混合数据源测试', "复杂配置description值不正确"
            assert case['priority'] == 'high', "复杂配置priority值不正确"
        
        info(f"复杂混合数据源测试通过，生成 {len(data)} 条数据")
    
    def test_mixed_data_source_merge_strategies_comparison(self):
        """测试不同合并策略的对比"""
        base_config = 'caseparams/test_chat_gateway.yaml'
        dynamic_query = 'db://mysql/test/SELECT 1 as user_id, "user1" as username UNION SELECT 2, "user2"'
        
        strategies = ['cross_product', 'append', 'override']
        results = {}
        
        for strategy in strategies:
            mixed_config = {
                'type': 'mixed',
                'name': f'{strategy}_test',
                'base_config': base_config,
                'dynamic_data_query': dynamic_query,
                'merge_strategy': strategy
            }
            
            # 切换到混合数据源
            success = data_source_switcher.switch_to(mixed_config)
            assert success, f"切换到{strategy}策略混合数据源失败"
            
            # 获取数据
            data = data_source_switcher.get_data()
            results[strategy] = len(data)
            
            # 验证数据格式
            for case in data:
                assert case['merge_strategy'] == strategy, f"{strategy}策略数据merge_strategy字段不正确"
                assert case['data_source'] == 'mixed', f"{strategy}策略数据data_source字段不正确"
        
        # 验证不同策略的数据量差异
        assert results['cross_product'] > results['append'], "笛卡尔积策略数据量应该大于追加策略"
        assert results['cross_product'] > results['override'], "笛卡尔积策略数据量应该大于覆盖策略"
        
        info(f"合并策略对比测试通过: {results}")
    
    def test_mixed_data_source_with_empty_data(self):
        """测试空数据的混合数据源"""
        # 测试只有基础数据的情况
        only_base_config = {
            'type': 'mixed',
            'name': 'only_base_test',
            'base_config': 'caseparams/test_chat_gateway.yaml',
            'merge_strategy': 'cross_product'
        }
        
        success = data_source_switcher.switch_to(only_base_config)
        assert success, "切换到只有基础数据的混合数据源失败"
        
        data = data_source_switcher.get_data()
        assert len(data) > 0, "只有基础数据的混合数据源应该返回数据"
        
        # 测试只有动态数据的情况
        only_dynamic_config = {
            'type': 'mixed',
            'name': 'only_dynamic_test',
            'dynamic_data_query': 'db://mysql/test/SELECT 1 as user_id, "user1" as username',
            'merge_strategy': 'cross_product'
        }
        
        success = data_source_switcher.switch_to(only_dynamic_config)
        assert success, "切换到只有动态数据的混合数据源失败"
        
        data = data_source_switcher.get_data()
        assert len(data) > 0, "只有动态数据的混合数据源应该返回数据"
        
        # 测试完全空数据的情况
        empty_config = {
            'type': 'mixed',
            'name': 'empty_test',
            'merge_strategy': 'cross_product'
        }
        
        success = data_source_switcher.switch_to(empty_config)
        assert success, "切换到空数据的混合数据源失败"
        
        data = data_source_switcher.get_data()
        assert len(data) == 0, "空数据的混合数据源应该返回空列表"
        
        info("空数据混合数据源测试通过")


# 全局测试清理
def test_cleanup():
    """测试清理"""
    # 清除缓存
    data_source_switcher.clear_cache()
    enhanced_data_source_switcher.clear_cache()
    
    info("混合数据源测试完成") 