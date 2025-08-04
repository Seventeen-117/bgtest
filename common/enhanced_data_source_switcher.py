# coding: utf-8
# @Author: bgtech
"""
增强版动态数据源切换管理器
实现性能优化、错误处理、监控、线程安全等功能
"""

import os
import sys
import time
import json
import yaml
import threading
from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps
from contextlib import contextmanager
from datetime import datetime, timedelta
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum

from common.log import info, error, debug, warn
from common.data_source import DataSourceManager, get_db_data, get_test_data_from_db, get_redis_value, set_redis_value
from common.get_caseparams import read_test_data


class DataSourceType(Enum):
    """数据源类型枚举"""
    FILE = "file"
    DATABASE = "database"
    REDIS = "redis"
    MIXED = "mixed"


class SwitchStatus(Enum):
    """切换状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    FALLBACK = "fallback"
    TIMEOUT = "timeout"


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0
    max_delay: float = 60.0


@dataclass
class CacheConfig:
    """缓存配置"""
    max_size: int = 100
    ttl: int = 3600
    enable_lru: bool = True


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                # 检查是否过期
                if time.time() - self._timestamps[key] > self.ttl:
                    del self._cache[key]
                    del self._timestamps[key]
                    return None
                
                # 移动到末尾（最近使用）
                value = self._cache.pop(key)
                self._cache[key] = value
                return value
            return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                # 更新现有值
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                # 移除最久未使用的项
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def clear(self, key: str = None) -> None:
        """清除缓存"""
        with self._lock:
            if key:
                if key in self._cache:
                    del self._cache[key]
                    del self._timestamps[key]
            else:
                self._cache.clear()
                self._timestamps.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class ConnectionPool:
    """连接池管理器"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connections = {}
        self._connection_locks = {}
        self._lock = threading.RLock()
    
    def get_connection(self, key: str, factory_func: Callable) -> Any:
        """获取连接"""
        with self._lock:
            if key not in self._connections:
                if len(self._connections) >= self.max_connections:
                    # 移除最旧的连接
                    oldest_key = next(iter(self._connections))
                    self._close_connection(oldest_key)
                
                self._connections[key] = factory_func()
                self._connection_locks[key] = threading.Lock()
            
            return self._connections[key]
    
    def _close_connection(self, key: str) -> None:
        """关闭连接"""
        if key in self._connections:
            try:
                conn = self._connections[key]
                if hasattr(conn, 'close'):
                    conn.close()
                del self._connections[key]
                del self._connection_locks[key]
            except Exception as e:
                error(f"关闭连接失败 {key}: {e}")
    
    def close_all(self) -> None:
        """关闭所有连接"""
        with self._lock:
            for key in list(self._connections.keys()):
                self._close_connection(key)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._metrics = {
            'switch_count': 0,
            'switch_success': 0,
            'switch_failed': 0,
            'total_switch_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': []
        }
        self._lock = threading.RLock()
    
    def record_switch(self, config: str, success: bool, duration: float) -> None:
        """记录切换指标"""
        with self._lock:
            self._metrics['switch_count'] += 1
            self._metrics['total_switch_time'] += duration
            
            if success:
                self._metrics['switch_success'] += 1
            else:
                self._metrics['switch_failed'] += 1
    
    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        with self._lock:
            self._metrics['cache_hits'] += 1
    
    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        with self._lock:
            self._metrics['cache_misses'] += 1
    
    def record_error(self, error_type: str, error_msg: str) -> None:
        """记录错误"""
        with self._lock:
            self._metrics['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'type': error_type,
                'message': error_msg
            })
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        with self._lock:
            metrics = self._metrics.copy()
            if metrics['switch_count'] > 0:
                metrics['avg_switch_time'] = metrics['total_switch_time'] / metrics['switch_count']
                metrics['success_rate'] = metrics['switch_success'] / metrics['switch_count']
            else:
                metrics['avg_switch_time'] = 0.0
                metrics['success_rate'] = 0.0
            
            if metrics['cache_hits'] + metrics['cache_misses'] > 0:
                metrics['cache_hit_rate'] = metrics['cache_hits'] / (metrics['cache_hits'] + metrics['cache_misses'])
            else:
                metrics['cache_hit_rate'] = 0.0
            
            return metrics


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self._health_cache = {}
        self._cache_ttl = 300  # 5分钟缓存
    
    def check_data_source(self, config: Dict[str, Any]) -> bool:
        """检查数据源健康状态"""
        cache_key = f"{config.get('type')}_{config.get('name', 'unknown')}"
        
        # 检查缓存
        if cache_key in self._health_cache:
            last_check, is_healthy = self._health_cache[cache_key]
            if time.time() - last_check < self._cache_ttl:
                return is_healthy
        
        # 执行健康检查
        is_healthy = self._perform_health_check(config)
        self._health_cache[cache_key] = (time.time(), is_healthy)
        
        return is_healthy
    
    def _perform_health_check(self, config: Dict[str, Any]) -> bool:
        """执行具体的健康检查"""
        try:
            if config['type'] == DataSourceType.FILE.value:
                return os.path.exists(config.get('path', ''))
            elif config['type'] == DataSourceType.DATABASE.value:
                # 简单的数据库连接测试
                test_sql = "SELECT 1"
                result = get_db_data(test_sql, config['db_type'], config['env'])
                return len(result) > 0
            elif config['type'] == DataSourceType.REDIS.value:
                # Redis连接测试
                test_key = "health_check"
                set_redis_value(test_key, "test", config['env'])
                value = get_redis_value(test_key, config['env'])
                return value == "test"
            else:
                return True
        except Exception as e:
            error(f"健康检查失败: {e}")
            return False


class EnhancedDataSourceSwitcher:
    """增强版动态数据源切换管理器"""
    
    def __init__(self, retry_config: RetryConfig = None, cache_config: CacheConfig = None):
        self._data_source_manager = DataSourceManager()
        self._current_data_source = None
        self._switch_history = []
        self._fallback_sources = []
        
        # 配置
        self._retry_config = retry_config or RetryConfig()
        self._cache_config = cache_config or CacheConfig()
        
        # 组件
        self._cache = LRUCache(self._cache_config.max_size, self._cache_config.ttl)
        self._connection_pool = ConnectionPool()
        self._metrics_collector = MetricsCollector()
        self._health_checker = HealthChecker()
        
        # 线程安全
        self._lock = threading.RLock()
        self._source_stack = []
    
    def switch_to(self, data_source_config: Union[str, Dict[str, Any]], 
                  cache_key: str = None, **kwargs) -> bool:
        """
        切换到指定的数据源
        :param data_source_config: 数据源配置
        :param cache_key: 缓存键
        :param kwargs: 其他参数
        :return: 切换是否成功
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # 解析配置
                if isinstance(data_source_config, str):
                    parsed_config = self._parse_data_source_string(data_source_config)
                else:
                    parsed_config = data_source_config
                
                # 健康检查
                if not self._health_checker.check_data_source(parsed_config):
                    self._metrics_collector.record_error("health_check_failed", f"数据源健康检查失败: {parsed_config}")
                    return False
                
                # 验证配置
                if not self._validate_data_source_config(parsed_config):
                    return False
                
                # 执行切换
                success = self._do_switch(parsed_config, cache_key, **kwargs)
                
                # 记录指标
                duration = time.time() - start_time
                self._metrics_collector.record_switch(str(data_source_config), success, duration)
                
                return success
                
        except Exception as e:
            duration = time.time() - start_time
            self._metrics_collector.record_switch(str(data_source_config), False, duration)
            self._metrics_collector.record_error("switch_exception", str(e))
            error(f"切换数据源失败: {e}")
            return False
    
    def switch_to_with_fallback(self, primary_config: str, fallback_configs: List[str]) -> bool:
        """
        带回退机制的数据源切换
        :param primary_config: 主要配置
        :param fallback_configs: 回退配置列表
        :return: 切换是否成功
        """
        all_configs = [primary_config] + fallback_configs
        
        for i, config in enumerate(all_configs):
            try:
                if self.switch_to(config):
                    if i > 0:  # 使用了回退配置
                        self._metrics_collector.record_error("fallback_used", f"使用回退配置: {config}")
                    return True
            except Exception as e:
                self._metrics_collector.record_error("fallback_failed", f"回退配置失败: {config}, 错误: {e}")
                continue
        
        return False
    
    def get_data(self, query: str = None, **kwargs) -> List[Dict[str, Any]]:
        """
        从当前数据源获取数据
        :param query: 查询语句或文件路径
        :param kwargs: 其他参数
        :return: 数据列表
        """
        if not self._current_data_source:
            error("当前没有激活的数据源")
            return []
        
        cache_key = kwargs.get('cache_key') or self._current_data_source.get('cache_key')
        
        # 尝试从缓存获取
        if cache_key:
            cached_data = self._cache.get(cache_key)
            if cached_data is not None:
                self._metrics_collector.record_cache_hit()
                return cached_data
            else:
                self._metrics_collector.record_cache_miss()
        
        # 执行重试机制获取数据
        return self._execute_with_retry(self._get_data_from_source, query, **kwargs)
    
    def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """
        带重试机制的操作执行
        :param operation: 要执行的操作
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 操作结果
        """
        return self._execute_with_retry(operation, *args, **kwargs)
    
    @contextmanager
    def temporary_switch(self, data_source_config: Union[str, Dict[str, Any]], **kwargs):
        """
        临时切换数据源的上下文管理器
        :param data_source_config: 数据源配置
        :param kwargs: 其他参数
        """
        with self._lock:
            original_source = self._current_data_source.copy() if self._current_data_source else None
            
            try:
                success = self.switch_to(data_source_config, **kwargs)
                if not success:
                    raise Exception(f"临时切换数据源失败: {data_source_config}")
                yield self
            finally:
                if original_source:
                    self._do_switch(original_source)
    
    def get_current_data_source(self) -> Optional[Dict[str, Any]]:
        """获取当前数据源配置"""
        with self._lock:
            return self._current_data_source.copy() if self._current_data_source else None
    
    def get_switch_history(self) -> List[Dict[str, Any]]:
        """获取切换历史"""
        with self._lock:
            return self._switch_history.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self._metrics_collector.get_metrics()
    
    def clear_cache(self, cache_key: str = None) -> None:
        """清除缓存"""
        self._cache.clear(cache_key)
    
    def close_all_connections(self) -> None:
        """关闭所有连接"""
        self._connection_pool.close_all()
    
    def _do_switch(self, config: Dict[str, Any], cache_key: str = None, **kwargs) -> bool:
        """执行实际的数据源切换"""
        try:
            # 更新当前数据源
            self._current_data_source = config
            
            # 记录切换历史
            self._switch_history.append({
                'timestamp': datetime.now().isoformat(),
                'config': config.copy(),
                'cache_key': cache_key
            })
            
            # 限制历史记录数量
            if len(self._switch_history) > 100:
                self._switch_history.pop(0)
            
            info(f"成功切换到数据源: {config.get('type', 'unknown')} - {config.get('name', 'unnamed')}")
            return True
            
        except Exception as e:
            error(f"切换数据源失败: {e}")
            return False
    
    def _execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """带重试机制的执行"""
        last_exception = None
        
        for attempt in range(self._retry_config.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self._retry_config.max_retries - 1:
                    delay = min(
                        self._retry_config.initial_delay * (self._retry_config.backoff_factor ** attempt),
                        self._retry_config.max_delay
                    )
                    warn(f"操作失败，{delay}秒后重试 (尝试 {attempt + 1}/{self._retry_config.max_retries}): {e}")
                    time.sleep(delay)
                else:
                    error(f"操作最终失败: {e}")
                    raise last_exception
    
    def _get_data_from_source(self, query: str = None, **kwargs) -> List[Dict[str, Any]]:
        """从数据源获取数据"""
        config = self._current_data_source
        cache_key = kwargs.get('cache_key') or config.get('cache_key')
        
        try:
            if config['type'] == DataSourceType.FILE.value:
                data = self._get_file_data(query or config.get('path'))
            elif config['type'] == DataSourceType.DATABASE.value:
                data = self._get_database_data(query or config.get('sql'))
            elif config['type'] == DataSourceType.REDIS.value:
                data = self._get_redis_data(query or config.get('key'))
            elif config['type'] == DataSourceType.MIXED.value:
                data = self._get_mixed_data()
            else:
                error(f"不支持的数据源类型: {config['type']}")
                return []
            
            # 缓存数据
            if cache_key and data:
                self._cache.set(cache_key, data)
            
            info(f"从数据源获取数据: {config.get('type')} - {config.get('name')} ({len(data)} 条)")
            return data
            
        except Exception as e:
            error(f"从数据源获取数据失败: {e}")
            return []
    
    def _get_file_data(self, file_path: str) -> List[Dict[str, Any]]:
        """从文件获取数据"""
        try:
            return read_test_data(file_path)
        except Exception as e:
            error(f"从文件获取数据失败: {e}")
            return []
    
    def _get_database_data(self, sql: str) -> List[Dict[str, Any]]:
        """从数据库获取数据"""
        config = self._current_data_source
        
        try:
            return get_test_data_from_db(
                sql=sql,
                db_type=config['db_type'],
                env=config['env'],
                cache_key=config.get('cache_key')
            )
        except Exception as e:
            error(f"从数据库获取数据失败: {e}")
            return []
    
    def _get_redis_data(self, key: str) -> List[Dict[str, Any]]:
        """从Redis获取数据"""
        config = self._current_data_source
        
        try:
            data = get_redis_value(key, config['env'])
            
            # 将Redis数据转换为列表格式
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    data = [{'value': data}]
            elif not isinstance(data, list):
                data = [{'value': data}]
            
            return data
            
        except Exception as e:
            error(f"从Redis获取数据失败: {e}")
            return []
    
    def _get_mixed_data(self) -> List[Dict[str, Any]]:
        """
        获取混合数据源数据
        支持文件数据 + 数据库数据的组合逻辑
        """
        config = self._current_data_source
        
        try:
            # 获取混合数据源配置
            base_config = config.get('base_config', {})
            dynamic_data_query = config.get('dynamic_data_query', '')
            merge_strategy = config.get('merge_strategy', 'cross_product')
            cache_config_key = config.get('cache_config_key', '')
            
            # 1. 加载基础数据（文件数据）
            base_data = []
            if base_config:
                if isinstance(base_config, str):
                    # 如果是字符串，直接作为文件路径
                    base_data = self._get_file_data(base_config)
                elif isinstance(base_config, dict):
                    # 如果是字典，提取文件路径
                    file_path = base_config.get('file_path') or base_config.get('path')
                    if file_path:
                        base_data = self._get_file_data(file_path)
                    else:
                        # 如果没有文件路径，将整个配置作为基础数据
                        base_data = [base_config]
            
            # 2. 加载动态数据（数据库数据）
            dynamic_data = []
            if dynamic_data_query:
                if dynamic_data_query.startswith('db://'):
                    # 解析数据库查询
                    parsed_config = self._parse_database_string(dynamic_data_query)
                    if parsed_config:
                        sql = parsed_config.get('sql', '')
                        if sql:
                            dynamic_data = self._get_database_data(sql)
                else:
                    # 直接作为SQL查询
                    dynamic_data = self._get_database_data(dynamic_data_query)
            
            # 3. 加载缓存配置（Redis数据）
            cache_config = {}
            if cache_config_key:
                try:
                    cache_value = get_redis_value(cache_config_key, config.get('env', 'test'))
                    if cache_value:
                        if isinstance(cache_value, str):
                            import json
                            cache_config = json.loads(cache_value)
                        else:
                            cache_config = cache_value
                except Exception as e:
                    error(f"加载缓存配置失败: {e}")
            
            # 4. 合并数据
            combined_data = self._merge_mixed_data(
                base_data, 
                dynamic_data, 
                cache_config, 
                merge_strategy
            )
            
            info(f"混合数据源加载完成: 基础数据 {len(base_data)} 条, 动态数据 {len(dynamic_data)} 条, 合并后 {len(combined_data)} 条")
            return combined_data
            
        except Exception as e:
            error(f"获取混合数据源数据失败: {e}")
            return []
    
    def _merge_mixed_data(self, base_data: List[Dict[str, Any]], 
                         dynamic_data: List[Dict[str, Any]], 
                         cache_config: Dict[str, Any],
                         merge_strategy: str = 'cross_product') -> List[Dict[str, Any]]:
        """
        合并混合数据
        :param base_data: 基础数据（文件数据）
        :param dynamic_data: 动态数据（数据库数据）
        :param cache_config: 缓存配置（Redis数据）
        :param merge_strategy: 合并策略
        :return: 合并后的数据
        """
        try:
            if not base_data and not dynamic_data:
                return []
            
            if merge_strategy == 'cross_product':
                return self._cross_product_merge(base_data, dynamic_data, cache_config)
            elif merge_strategy == 'append':
                return self._append_merge(base_data, dynamic_data, cache_config)
            elif merge_strategy == 'override':
                return self._override_merge(base_data, dynamic_data, cache_config)
            else:
                # 默认使用笛卡尔积合并
                return self._cross_product_merge(base_data, dynamic_data, cache_config)
                
        except Exception as e:
            error(f"合并混合数据失败: {e}")
            return []
    
    def _cross_product_merge(self, base_data: List[Dict[str, Any]], 
                            dynamic_data: List[Dict[str, Any]], 
                            cache_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        笛卡尔积合并：为每个基础数据创建多个测试用例（基于动态数据）
        """
        merged_data = []
        
        # 如果没有基础数据，使用动态数据作为基础
        if not base_data and dynamic_data:
            for db_case in dynamic_data:
                merged_case = db_case.copy()
                merged_case.update(cache_config)
                merged_case['data_source'] = 'mixed'
                merged_case['merge_strategy'] = 'cross_product'
                merged_data.append(merged_case)
            return merged_data
        
        # 如果没有动态数据，使用基础数据
        if not dynamic_data and base_data:
            for base_case in base_data:
                merged_case = base_case.copy()
                merged_case.update(cache_config)
                merged_case['data_source'] = 'mixed'
                merged_case['merge_strategy'] = 'cross_product'
                merged_data.append(merged_case)
            return merged_data
        
        # 笛卡尔积合并
        for base_case in base_data:
            for db_case in dynamic_data:
                # 合并基础数据和动态数据
                merged_case = base_case.copy()
                merged_case.update(db_case)
                merged_case.update(cache_config)
                merged_case['data_source'] = 'mixed'
                merged_case['merge_strategy'] = 'cross_product'
                merged_data.append(merged_case)
        
        return merged_data
    
    def _append_merge(self, base_data: List[Dict[str, Any]], 
                     dynamic_data: List[Dict[str, Any]], 
                     cache_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        追加合并：将动态数据追加到基础数据后面
        """
        merged_data = []
        
        # 添加基础数据
        for base_case in base_data:
            merged_case = base_case.copy()
            merged_case.update(cache_config)
            merged_case['data_source'] = 'mixed'
            merged_case['merge_strategy'] = 'append'
            merged_data.append(merged_case)
        
        # 添加动态数据
        for db_case in dynamic_data:
            merged_case = db_case.copy()
            merged_case.update(cache_config)
            merged_case['data_source'] = 'mixed'
            merged_case['merge_strategy'] = 'append'
            merged_data.append(merged_case)
        
        return merged_data
    
    def _override_merge(self, base_data: List[Dict[str, Any]], 
                       dynamic_data: List[Dict[str, Any]], 
                       cache_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        覆盖合并：动态数据覆盖基础数据中的相同字段
        """
        merged_data = []
        
        # 如果没有基础数据，使用动态数据
        if not base_data and dynamic_data:
            for db_case in dynamic_data:
                merged_case = db_case.copy()
                merged_case.update(cache_config)
                merged_case['data_source'] = 'mixed'
                merged_case['merge_strategy'] = 'override'
                merged_data.append(merged_case)
            return merged_data
        
        # 如果没有动态数据，使用基础数据
        if not dynamic_data and base_data:
            for base_case in base_data:
                merged_case = base_case.copy()
                merged_case.update(cache_config)
                merged_case['data_source'] = 'mixed'
                merged_case['merge_strategy'] = 'override'
                merged_data.append(merged_case)
            return merged_data
        
        # 覆盖合并：动态数据覆盖基础数据
        for i, base_case in enumerate(base_data):
            merged_case = base_case.copy()
            
            # 如果有对应的动态数据，进行覆盖
            if i < len(dynamic_data):
                merged_case.update(dynamic_data[i])
            
            merged_case.update(cache_config)
            merged_case['data_source'] = 'mixed'
            merged_case['merge_strategy'] = 'override'
            merged_data.append(merged_case)
        
        # 如果动态数据比基础数据多，添加剩余的动态数据
        for i in range(len(base_data), len(dynamic_data)):
            merged_case = dynamic_data[i].copy()
            merged_case.update(cache_config)
            merged_case['data_source'] = 'mixed'
            merged_case['merge_strategy'] = 'override'
            merged_data.append(merged_case)
        
        return merged_data
    
    def _parse_data_source_string(self, data_source_str: str) -> Dict[str, Any]:
        """解析数据源配置字符串"""
        try:
            if data_source_str.startswith('db://'):
                return self._parse_database_string(data_source_str)
            elif data_source_str.startswith('redis://'):
                return self._parse_redis_string(data_source_str)
            elif data_source_str.startswith('file://'):
                return self._parse_file_string(data_source_str)
            else:
                # 默认为文件路径
                return self._parse_file_string(data_source_str)
        except Exception as e:
            error(f"解析数据源配置字符串失败: {e}")
            return {}
    
    def _parse_database_string(self, db_string: str) -> Dict[str, Any]:
        """解析数据库配置字符串"""
        try:
            config_part = db_string[6:]  # 移除 db:// 前缀
            
            # 分离查询参数
            if '?' in config_part:
                main_part, params_part = config_part.split('?', 1)
                params = dict(item.split('=') for item in params_part.split('&'))
            else:
                main_part = config_part
                params = {}
            
            # 解析主要部分
            parts = main_part.split('/', 2)
            if len(parts) < 2:
                raise ValueError("数据库配置格式错误")
            
            db_type = parts[0]
            env = parts[1]
            sql = parts[2] if len(parts) > 2 else ""
            
            return {
                'type': DataSourceType.DATABASE.value,
                'db_type': db_type,
                'env': env,
                'sql': sql,
                'cache_key': params.get('cache_key'),
                'name': f"{db_type}_{env}"
            }
            
        except Exception as e:
            error(f"解析数据库配置字符串失败: {e}")
            return {}
    
    def _parse_redis_string(self, redis_string: str) -> Dict[str, Any]:
        """解析Redis配置字符串"""
        try:
            config_part = redis_string[8:]  # 移除 redis:// 前缀
            parts = config_part.split('/', 1)
            
            if len(parts) < 2:
                raise ValueError("Redis配置格式错误")
            
            env, key = parts[0], parts[1]
            
            return {
                'type': DataSourceType.REDIS.value,
                'env': env,
                'key': key,
                'name': f"redis_{env}"
            }
            
        except Exception as e:
            error(f"解析Redis配置字符串失败: {e}")
            return {}
    
    def _parse_file_string(self, file_string: str) -> Dict[str, Any]:
        """解析文件配置字符串"""
        try:
            path = file_string[7:] if file_string.startswith('file://') else file_string
            
            return {
                'type': DataSourceType.FILE.value,
                'path': path,
                'name': f"file_{os.path.basename(path)}"
            }
            
        except Exception as e:
            error(f"解析文件配置字符串失败: {e}")
            return {}
    
    def _validate_data_source_config(self, config: Dict[str, Any]) -> bool:
        """验证数据源配置"""
        if not config or 'type' not in config:
            error("数据源配置缺少type字段")
            return False
        
        data_source_type = config['type']
        
        if data_source_type == DataSourceType.DATABASE.value:
            required_fields = ['db_type', 'env']
            for field in required_fields:
                if field not in config:
                    error(f"数据库配置缺少必需字段: {field}")
                    return False
        
        elif data_source_type == DataSourceType.REDIS.value:
            required_fields = ['env', 'key']
            for field in required_fields:
                if field not in config:
                    error(f"Redis配置缺少必需字段: {field}")
                    return False
        
        elif data_source_type == DataSourceType.FILE.value:
            if 'path' not in config:
                error("文件配置缺少path字段")
                return False
        
        return True


# 全局增强版数据源切换器实例
enhanced_data_source_switcher = EnhancedDataSourceSwitcher()


def switch_data_source(data_source_config: Union[str, Dict[str, Any]], **kwargs):
    """
    数据源切换装饰器
    :param data_source_config: 数据源配置
    :param kwargs: 其他参数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **func_kwargs):
            # 切换到指定数据源
            success = enhanced_data_source_switcher.switch_to(data_source_config, **kwargs)
            if not success:
                raise Exception(f"无法切换到数据源: {data_source_config}")
            
            try:
                # 执行测试函数
                return func(*args, **func_kwargs)
            finally:
                # 测试完成后可以在这里做一些清理工作
                pass
        
        return wrapper
    return decorator


def with_data_source(data_source_config: Union[str, Dict[str, Any]], **kwargs):
    """
    临时数据源上下文管理器
    :param data_source_config: 数据源配置
    :param kwargs: 其他参数
    """
    return enhanced_data_source_switcher.temporary_switch(data_source_config, **kwargs)


# 便捷函数
def get_current_data_source():
    """获取当前数据源配置"""
    return enhanced_data_source_switcher.get_current_data_source()


def get_data_from_current_source(query: str = None, **kwargs):
    """从当前数据源获取数据"""
    return enhanced_data_source_switcher.get_data(query, **kwargs)


def execute_query_on_current_source(query: str, **kwargs):
    """在当前数据源上执行查询"""
    return enhanced_data_source_switcher.execute_with_retry(
        enhanced_data_source_switcher._get_data_from_source, query, **kwargs
    )


def get_switcher_metrics():
    """获取切换器性能指标"""
    return enhanced_data_source_switcher.get_metrics()


def clear_switcher_cache(cache_key: str = None):
    """清除切换器缓存"""
    enhanced_data_source_switcher.clear_cache(cache_key) 