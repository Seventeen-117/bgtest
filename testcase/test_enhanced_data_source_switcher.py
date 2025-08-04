# coding: utf-8
# @Author: bgtech
"""
增强版数据源切换器测试用例
测试性能优化、错误处理、监控、线程安全等功能
"""

import pytest
import time
import threading
import allure
from concurrent.futures import ThreadPoolExecutor, as_completed
from common.enhanced_data_source_switcher import (
    EnhancedDataSourceSwitcher, 
    RetryConfig, 
    CacheConfig,
    enhanced_data_source_switcher,
    get_switcher_metrics,
    clear_switcher_cache
)
from common.fluent_data_source_switcher import (
    FluentDataSourceSwitcher,
    from_file,
    from_database,
    from_redis,
    get_fluent_metrics, clear_fluent_cache
)
from common.log import info, error, debug


class TestEnhancedDataSourceSwitcher:
    """增强版数据源切换器测试"""
    
    def test_basic_functionality(self):
        """测试基础功能"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 测试文件数据源
        success = switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "切换到文件数据源失败"
        
        data = switcher.get_data()
        assert len(data) > 0, "从文件数据源获取数据失败"
        
        # 验证当前数据源配置
        current_config = switcher.get_current_data_source()
        assert current_config['type'] == 'file'
        assert 'test_chat_gateway.yaml' in current_config['path']
        
        info(f"基础功能测试通过，获取到 {len(data)} 条数据")
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 第一次获取数据（会缓存）
        switcher.switch_to("caseparams/test_chat_gateway.yaml")
        data1 = switcher.get_data(cache_key="test_cache")
        
        # 第二次获取数据（从缓存）
        data2 = switcher.get_data(cache_key="test_cache")
        
        assert data1 == data2, "缓存数据不一致"
        
        # 清除缓存
        switcher.clear_cache("test_cache")
        data3 = switcher.get_data(cache_key="test_cache")
        
        # 清除缓存后应该重新获取数据
        assert data1 == data3, "清除缓存后数据不一致"
        
        info("缓存功能测试通过")
    
    def test_retry_mechanism(self):
        """测试重试机制"""
        retry_config = RetryConfig(max_retries=3, backoff_factor=1.0, initial_delay=0.1)
        switcher = EnhancedDataSourceSwitcher(retry_config=retry_config)
        
        # 测试一个会失败的操作
        def failing_operation():
            raise Exception("模拟失败操作")
        
        # 应该重试3次后最终失败
        with pytest.raises(Exception):
            switcher.execute_with_retry(failing_operation)
        
        info("重试机制测试通过")
    
    def test_health_check(self):
        """测试健康检查"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 测试有效的文件路径
        success = switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "健康检查应该通过有效的文件路径"
        
        # 测试无效的文件路径
        success = switcher.switch_to("caseparams/nonexistent_file.yaml")
        assert not success, "健康检查应该拒绝无效的文件路径"
        
        info("健康检查测试通过")
    
    def test_metrics_collection(self):
        """测试指标收集"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 执行一些操作
        switcher.switch_to("caseparams/test_chat_gateway.yaml")
        switcher.get_data()
        
        # 获取指标
        metrics = switcher.get_metrics()
        
        assert 'switch_count' in metrics
        assert 'switch_success' in metrics
        assert 'cache_hits' in metrics
        assert 'cache_misses' in metrics
        assert 'avg_switch_time' in metrics
        assert 'success_rate' in metrics
        
        assert metrics['switch_count'] > 0
        assert metrics['success_rate'] > 0
        
        info(f"指标收集测试通过: {metrics}")
    
    def test_thread_safety(self):
        """测试线程安全"""
        switcher = EnhancedDataSourceSwitcher()
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                # 每个线程执行切换和数据获取
                success = switcher.switch_to("caseparams/test_chat_gateway.yaml")
                if success:
                    data = switcher.get_data()
                    results.append((worker_id, len(data)))
                else:
                    errors.append(f"Worker {worker_id} 切换失败")
            except Exception as e:
                errors.append(f"Worker {worker_id} 异常: {e}")
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证结果
        assert len(errors) == 0, f"线程安全测试失败，错误: {errors}"
        assert len(results) == 5, "应该有5个线程成功执行"
        
        info(f"线程安全测试通过，结果: {results}")
    
    def test_fallback_mechanism(self):
        """测试回退机制"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 主要配置（有效）
        primary_config = "caseparams/test_chat_gateway.yaml"
        # 回退配置（无效）
        fallback_configs = ["caseparams/nonexistent1.yaml", "caseparams/nonexistent2.yaml"]
        
        # 应该使用主要配置成功
        success = switcher.switch_to_with_fallback(primary_config, fallback_configs)
        assert success, "回退机制应该使用主要配置成功"
        
        # 测试所有配置都失败的情况
        all_invalid_configs = ["caseparams/nonexistent1.yaml", "caseparams/nonexistent2.yaml"]
        success = switcher.switch_to_with_fallback(all_invalid_configs[0], all_invalid_configs[1:])
        assert not success, "所有配置都无效时应该失败"
        
        info("回退机制测试通过")
    
    def test_temporary_switch(self):
        """测试临时切换"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 记录原始配置
        switcher.switch_to("caseparams/test_chat_gateway.yaml")
        original_config = switcher.get_current_data_source()
        
        # 使用临时切换
        with switcher.temporary_switch("caseparams/test_chat_gateway.yaml"):
            temp_config = switcher.get_current_data_source()
            assert temp_config['path'] == "caseparams/test_chat_gateway.yaml"
        
        # 验证恢复原始配置
        current_config = switcher.get_current_data_source()
        assert current_config['path'] == original_config['path']
        
        info("临时切换测试通过")
    
    def test_performance_under_load(self):
        """测试负载下的性能"""
        switcher = EnhancedDataSourceSwitcher()
        
        start_time = time.time()
        operations = 100
        
        for i in range(operations):
            switcher.switch_to("caseparams/test_chat_gateway.yaml")
            data = switcher.get_data()
            assert len(data) > 0
        
        total_time = time.time() - start_time
        avg_time = total_time / operations
        
        # 平均每次操作应该在合理时间内完成
        assert avg_time < 0.1, f"平均操作时间过长: {avg_time:.4f}s"
        
        info(f"性能测试通过: {operations} 次操作，平均时间 {avg_time:.4f}s")
    
    def test_concurrent_operations(self):
        """测试并发操作"""
        switcher = EnhancedDataSourceSwitcher()
        
        def concurrent_operation(worker_id):
            try:
                for i in range(10):
                    success = switcher.switch_to("caseparams/test_chat_gateway.yaml")
                    if success:
                        data = switcher.get_data()
                        assert len(data) > 0
                    time.sleep(0.01)  # 模拟工作负载
                return f"Worker {worker_id} 完成"
            except Exception as e:
                return f"Worker {worker_id} 失败: {e}"
        
        # 使用线程池执行并发操作
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(concurrent_operation, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # 验证所有操作都成功
        success_count = sum(1 for result in results if "完成" in result)
        assert success_count == 5, f"并发操作失败: {results}"
        
        info(f"并发操作测试通过: {results}")


class TestFluentDataSourceSwitcher:
    """流式数据源切换器测试"""
    
    def test_fluent_api_basic(self):
        """测试流式API基础功能"""
        # 从文件开始
        data = (from_file("caseparams/test_chat_gateway.yaml")
                .with_cache("fluent_test", 1800)
                .execute())
        
        assert len(data) > 0, "流式API获取数据失败"
        
        # 验证操作链
        switcher = from_file("caseparams/test_chat_gateway.yaml")
        switcher.with_cache("test", 1800)
        operation_chain = switcher.get_operation_chain()
        
        assert "from_file" in operation_chain[0]
        assert "with_cache" in operation_chain[1]
        
        info(f"流式API基础功能测试通过，获取到 {len(data)} 条数据")
    
    def test_fluent_api_database(self):
        """测试流式API数据库功能"""
        # 从数据库开始
        switcher = (from_database("mysql", "test")
                   .with_sql("SELECT 1 as test")
                   .with_cache("db_test", 3600))
        
        # 执行切换
        success = switcher.switch()
        assert success, "数据库切换失败"
        
        # 获取数据
        data = switcher.execute()
        assert len(data) > 0, "数据库数据获取失败"
        
        info(f"流式API数据库功能测试通过，获取到 {len(data)} 条数据")
    
    def test_fluent_api_redis(self):
        """测试流式API Redis功能"""
        # 从Redis开始
        switcher = (from_redis("test")
                   .with_key("test:user:123")
                   .with_cache("redis_test", 1800))
        
        # 执行切换
        success = switcher.switch()
        assert success, "Redis切换失败"
        
        info("流式API Redis功能测试通过")
    
    def test_fluent_api_with_retry(self):
        """测试流式API重试功能"""
        # 配置重试策略
        switcher = (from_file("caseparams/test_chat_gateway.yaml")
                   .with_retry(max_retries=3, backoff_factor=1.5)
                   .with_cache("retry_test"))
        
        data = switcher.execute()
        assert len(data) > 0, "重试功能测试失败"
        
        info("流式API重试功能测试通过")
    
    def test_fluent_api_with_fallback(self):
        """测试流式API回退功能"""
        # 配置回退策略
        switcher = (from_file("caseparams/test_chat_gateway.yaml")
                   .with_fallback("caseparams/test_chat_gateway.yaml")
                   .with_cache("fallback_test"))
        
        data = switcher.execute()
        assert len(data) > 0, "回退功能测试失败"
        
        info("流式API回退功能测试通过")
    
    def test_fluent_api_temporary(self):
        """测试流式API临时切换"""
        # 使用临时切换
        with from_file("caseparams/test_chat_gateway.yaml").temporary() as switcher:
            data = switcher.execute()
            assert len(data) > 0, "临时切换测试失败"
        
        info("流式API临时切换测试通过")
    
    def test_fluent_api_metrics(self):
        """测试流式API指标收集"""
        # 执行一些操作
        from_file("caseparams/test_chat_gateway.yaml").execute()
        from_database("mysql", "test").with_sql("SELECT 1").execute()
        
        # 获取指标
        metrics = get_fluent_metrics()
        
        assert 'switch_count' in metrics
        assert 'switch_success' in metrics
        assert metrics['switch_count'] > 0
        
        info(f"流式API指标收集测试通过: {metrics}")


class TestEnhancedDataSourceSwitcherIntegration:
    """增强版数据源切换器集成测试"""
    
    def test_integration_with_existing_framework(self):
        """测试与现有框架的集成"""
        # 使用增强版切换器
        switcher = EnhancedDataSourceSwitcher()
        
        # 切换到文件数据源
        success = switcher.switch_to("caseparams/test_chat_gateway.yaml")
        assert success, "集成测试切换失败"
        
        # 获取数据
        data = switcher.get_data()
        assert len(data) > 0, "集成测试数据获取失败"
        
        # 验证数据格式
        for case in data:
            assert 'case_id' in case, "数据格式验证失败"
            assert 'url' in case, "数据格式验证失败"
            assert 'method' in case, "数据格式验证失败"
        
        info(f"集成测试通过，处理了 {len(data)} 条数据")
    
    def test_performance_comparison(self):
        """性能对比测试"""
        # 测试增强版切换器性能
        enhanced_switcher = EnhancedDataSourceSwitcher()
        
        start_time = time.time()
        for i in range(50):
            enhanced_switcher.switch_to("caseparams/test_chat_gateway.yaml")
            enhanced_switcher.get_data()
        
        enhanced_time = time.time() - start_time
        
        # 测试流式API性能
        fluent_switcher = FluentDataSourceSwitcher()
        
        start_time = time.time()
        for i in range(50):
            fluent_switcher.from_file("caseparams/test_chat_gateway.yaml").execute()
        
        fluent_time = time.time() - start_time
        
        info(f"性能对比: 增强版 {enhanced_time:.4f}s, 流式API {fluent_time:.4f}s")
        
        # 两种方式都应该在合理时间内完成
        assert enhanced_time < 5.0, f"增强版切换器性能过慢: {enhanced_time:.4f}s"
        assert fluent_time < 5.0, f"流式API性能过慢: {fluent_time:.4f}s"
    
    def test_error_handling_comprehensive(self):
        """综合错误处理测试"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 测试各种错误情况
        error_cases = [
            ("无效文件路径", "caseparams/nonexistent.yaml"),
            ("无效数据库配置", "db://invalid/test/SELECT 1"),
            ("无效Redis配置", "redis://invalid/nonexistent_key"),
        ]
        
        for case_name, config in error_cases:
            success = switcher.switch_to(config)
            assert not success, f"{case_name} 应该失败但成功了"
        
        # 测试异常处理
        try:
            switcher.get_data()  # 没有激活的数据源
        except Exception as e:
            assert "没有激活的数据源" in str(e) or "当前没有激活的数据源" in str(e)
        
        info("综合错误处理测试通过")
    
    def test_cache_management(self):
        """缓存管理测试"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 测试缓存设置和获取
        switcher.switch_to("caseparams/test_chat_gateway.yaml")
        data1 = switcher.get_data(cache_key="management_test")
        
        # 清除特定缓存
        switcher.clear_cache("management_test")
        
        # 重新获取数据
        data2 = switcher.get_data(cache_key="management_test")
        
        # 数据应该相同（重新加载）
        assert data1 == data2, "缓存管理测试失败"
        
        # 清除所有缓存
        switcher.clear_cache()
        
        info("缓存管理测试通过")
    
    def test_metrics_and_monitoring(self):
        """指标和监控测试"""
        switcher = EnhancedDataSourceSwitcher()
        
        # 执行一系列操作
        operations = [
            ("caseparams/test_chat_gateway.yaml", "file_test"),
            ("caseparams/test_chat_gateway.yaml", "file_test2"),
        ]
        
        for config, cache_key in operations:
            switcher.switch_to(config)
            switcher.get_data(cache_key=cache_key)
        
        # 获取指标
        metrics = switcher.get_metrics()
        
        # 验证指标
        assert metrics['switch_count'] >= 2
        assert metrics['switch_success'] >= 2
        assert metrics['success_rate'] > 0.8  # 成功率应该很高
        assert metrics['avg_switch_time'] > 0  # 平均切换时间应该大于0
        
        info(f"指标和监控测试通过: {metrics}")


# 全局测试清理
def test_cleanup():
    """测试清理"""
    # 清除所有缓存
    clear_switcher_cache()
    clear_fluent_cache()
    
    # 获取最终指标
    enhanced_metrics = get_switcher_metrics()
    fluent_metrics = get_fluent_metrics()
    
    info(f"测试完成，最终指标 - 增强版: {enhanced_metrics}")
    info(f"测试完成，最终指标 - 流式API: {fluent_metrics}") 