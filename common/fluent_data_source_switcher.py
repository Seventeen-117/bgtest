# coding: utf-8
# @Author: bgtech
"""
流式数据源切换器
提供链式调用API，使数据源切换更加直观和易用
"""

import os
import time
from typing import Dict, Any, List, Optional, Union, Callable
from contextlib import contextmanager
from common.enhanced_data_source_switcher import EnhancedDataSourceSwitcher, RetryConfig, CacheConfig
from common.log import info, error, debug


class FluentDataSourceSwitcher:
    """流式数据源切换器"""
    
    def __init__(self, retry_config: RetryConfig = None, cache_config: CacheConfig = None):
        self._switcher = EnhancedDataSourceSwitcher(retry_config, cache_config)
        self._current_config = None
        self._operation_chain = []
        self._cache_key = None
        self._cache_ttl = 3600
    
    def from_file(self, path: str) -> 'FluentDataSourceSwitcher':
        """
        从文件数据源开始
        :param path: 文件路径
        :return: 流式切换器实例
        """
        self._current_config = {
            'type': 'file',
            'path': path,
            'name': f"file_{os.path.basename(path)}"
        }
        self._operation_chain.append(f"from_file({path})")
        return self
    
    def from_database(self, db_type: str, env: str = 'test') -> 'FluentDataSourceSwitcher':
        """
        从数据库数据源开始
        :param db_type: 数据库类型
        :param env: 环境
        :return: 流式切换器实例
        """
        self._current_config = {
            'type': 'database',
            'db_type': db_type,
            'env': env,
            'name': f"{db_type}_{env}"
        }
        self._operation_chain.append(f"from_database({db_type}, {env})")
        return self
    
    def from_redis(self, env: str = 'test') -> 'FluentDataSourceSwitcher':
        """
        从Redis数据源开始
        :param env: 环境
        :return: 流式切换器实例
        """
        self._current_config = {
            'type': 'redis',
            'env': env,
            'name': f"redis_{env}"
        }
        self._operation_chain.append(f"from_redis({env})")
        return self
    
    def with_sql(self, sql: str) -> 'FluentDataSourceSwitcher':
        """
        配置SQL查询
        :param sql: SQL语句
        :return: 流式切换器实例
        """
        if self._current_config and self._current_config['type'] == 'database':
            self._current_config['sql'] = sql
            self._operation_chain.append(f"with_sql({sql[:50]}...)")
        else:
            error("SQL配置只能用于数据库数据源")
        return self
    
    def with_key(self, key: str) -> 'FluentDataSourceSwitcher':
        """
        配置Redis键
        :param key: Redis键
        :return: 流式切换器实例
        """
        if self._current_config and self._current_config['type'] == 'redis':
            self._current_config['key'] = key
            self._operation_chain.append(f"with_key({key})")
        else:
            error("键配置只能用于Redis数据源")
        return self
    
    def with_cache(self, cache_key: str, ttl: int = 3600) -> 'FluentDataSourceSwitcher':
        """
        配置缓存
        :param cache_key: 缓存键
        :param ttl: 缓存时间（秒）
        :return: 流式切换器实例
        """
        self._cache_key = cache_key
        self._cache_ttl = ttl
        self._operation_chain.append(f"with_cache({cache_key}, {ttl})")
        return self
    
    def with_retry(self, max_retries: int = 3, backoff_factor: float = 2.0) -> 'FluentDataSourceSwitcher':
        """
        配置重试策略
        :param max_retries: 最大重试次数
        :param backoff_factor: 退避因子
        :return: 流式切换器实例
        """
        retry_config = RetryConfig(max_retries=max_retries, backoff_factor=backoff_factor)
        self._switcher = EnhancedDataSourceSwitcher(retry_config)
        self._operation_chain.append(f"with_retry({max_retries}, {backoff_factor})")
        return self
    
    def with_fallback(self, *fallback_configs: str) -> 'FluentDataSourceSwitcher':
        """
        配置回退数据源
        :param fallback_configs: 回退配置列表
        :return: 流式切换器实例
        """
        self._fallback_configs = list(fallback_configs)
        self._operation_chain.append(f"with_fallback({len(fallback_configs)} configs)")
        return self
    
    def execute(self) -> List[Dict[str, Any]]:
        """
        执行并获取数据
        :return: 数据列表
        """
        if not self._current_config:
            raise ValueError("未配置数据源，请先调用 from_file(), from_database() 或 from_redis()")
        
        # 构建配置字符串
        config_str = self._build_config_string()
        
        # 执行切换
        if hasattr(self, '_fallback_configs'):
            success = self._switcher.switch_to_with_fallback(config_str, self._fallback_configs)
        else:
            success = self._switcher.switch_to(config_str, cache_key=self._cache_key)
        
        if not success:
            raise Exception(f"数据源切换失败: {config_str}")
        
        # 获取数据
        return self._switcher.get_data()
    
    def execute_with_query(self, query: str) -> List[Dict[str, Any]]:
        """
        执行指定查询并获取数据
        :param query: 查询语句
        :return: 数据列表
        """
        if not self._current_config:
            raise ValueError("未配置数据源")
        
        # 构建配置字符串
        config_str = self._build_config_string()
        
        # 执行切换
        success = self._switcher.switch_to(config_str, cache_key=self._cache_key)
        if not success:
            raise Exception(f"数据源切换失败: {config_str}")
        
        # 获取数据
        return self._switcher.get_data(query)
    
    def switch(self) -> bool:
        """
        仅执行切换，不获取数据
        :return: 切换是否成功
        """
        if not self._current_config:
            raise ValueError("未配置数据源")
        
        config_str = self._build_config_string()
        
        if hasattr(self, '_fallback_configs'):
            return self._switcher.switch_to_with_fallback(config_str, self._fallback_configs)
        else:
            return self._switcher.switch_to(config_str, cache_key=self._cache_key)
    
    @contextmanager
    def temporary(self):
        """
        临时切换数据源的上下文管理器
        :return: 上下文管理器
        """
        if not self._current_config:
            raise ValueError("未配置数据源")
        
        config_str = self._build_config_string()
        
        with self._switcher.temporary_switch(config_str, cache_key=self._cache_key):
            yield self
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self._switcher.get_metrics()
    
    def get_operation_chain(self) -> List[str]:
        """获取操作链"""
        return self._operation_chain.copy()
    
    def clear_cache(self, cache_key: str = None) -> 'FluentDataSourceSwitcher':
        """清除缓存"""
        self._switcher.clear_cache(cache_key)
        return self
    
    def _build_config_string(self) -> str:
        """构建配置字符串"""
        if not self._current_config:
            return ""
        
        config_type = self._current_config['type']
        
        if config_type == 'file':
            return self._current_config['path']
        
        elif config_type == 'database':
            db_type = self._current_config['db_type']
            env = self._current_config['env']
            sql = self._current_config.get('sql', '')
            
            config_str = f"db://{db_type}/{env}"
            if sql:
                config_str += f"/{sql}"
            
            if self._cache_key:
                config_str += f"?cache_key={self._cache_key}"
                if self._cache_ttl != 3600:
                    config_str += f"&ttl={self._cache_ttl}"
            
            return config_str
        
        elif config_type == 'redis':
            env = self._current_config['env']
            key = self._current_config.get('key', '')
            
            if not key:
                raise ValueError("Redis数据源需要配置键")
            
            return f"redis://{env}/{key}"
        
        else:
            raise ValueError(f"不支持的数据源类型: {config_type}")


# 全局流式数据源切换器实例
fluent_switcher = FluentDataSourceSwitcher()


# 便捷函数
def from_file(path: str) -> FluentDataSourceSwitcher:
    """从文件开始"""
    return FluentDataSourceSwitcher().from_file(path)


def from_database(db_type: str, env: str = 'test') -> FluentDataSourceSwitcher:
    """从数据库开始"""
    return FluentDataSourceSwitcher().from_database(db_type, env)


def from_redis(env: str = 'test') -> FluentDataSourceSwitcher:
    """从Redis开始"""
    return FluentDataSourceSwitcher().from_redis(env)


def get_fluent_metrics() -> Dict[str, Any]:
    """获取流式切换器指标"""
    return fluent_switcher.get_metrics()


def clear_fluent_cache(cache_key: str = None) -> None:
    """清除流式切换器缓存"""
    fluent_switcher.clear_cache(cache_key) 