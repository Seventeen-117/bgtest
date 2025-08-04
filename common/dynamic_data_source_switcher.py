# coding: utf-8
# @Author: bgtech
"""
动态数据源切换管理器
支持在测试用例中动态切换不同的数据源
"""

import json
import os
from contextlib import contextmanager
from functools import wraps
from typing import Dict, Any, List, Optional, Union

from common.data_source import DataSourceManager, get_db_data, get_test_data_from_db, get_redis_value, set_redis_value
from common.get_caseparams import read_test_data
from common.log import info, error


class DynamicDataSourceSwitcher:
    """动态数据源切换管理器"""
    
    def __init__(self):
        self._data_source_manager = DataSourceManager()
        self._current_data_source = None
        self._data_source_cache = {}
        self._switch_history = []
        
    def switch_to(self, data_source_config: Union[str, Dict[str, Any]], 
                  cache_key: str = None, **kwargs) -> bool:
        """
        切换到指定的数据源
        :param data_source_config: 数据源配置
        :param cache_key: 缓存键
        :param kwargs: 其他参数
        :return: 切换是否成功
        """
        try:
            if isinstance(data_source_config, str):
                # 解析数据源配置字符串
                parsed_config = self._parse_data_source_string(data_source_config)
            else:
                parsed_config = data_source_config
            
            # 验证数据源配置
            if not self._validate_data_source_config(parsed_config):
                return False
            
            # 切换到新数据源
            self._current_data_source = parsed_config
            self._switch_history.append({
                'timestamp': self._get_current_timestamp(),
                'config': parsed_config.copy()
            })
            
            info(f"成功切换到数据源: {parsed_config.get('type', 'unknown')} - {parsed_config.get('name', 'unnamed')}")
            return True
            
        except Exception as e:
            error(f"切换数据源失败: {e}")
            return False
    
    def get_current_data_source(self) -> Optional[Dict[str, Any]]:
        """获取当前数据源配置"""
        return self._current_data_source
    
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
        
        data_source_type = self._current_data_source.get('type')
        cache_key = kwargs.get('cache_key') or self._current_data_source.get('cache_key')
        
        try:
            if data_source_type == 'file':
                return self._get_file_data(query or self._current_data_source.get('path'))
            elif data_source_type == 'database':
                return self._get_database_data(query or self._current_data_source.get('sql'))
            elif data_source_type == 'redis':
                return self._get_redis_data(query or self._current_data_source.get('key'))
            elif data_source_type == 'mixed':
                return self._get_mixed_data()
            else:
                error(f"不支持的数据源类型: {data_source_type}")
                return []
                
        except Exception as e:
            error(f"从数据源获取数据失败: {e}")
            return []
    
    def execute_query(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        执行查询（根据当前数据源类型）
        :param query: 查询语句
        :param kwargs: 其他参数
        :return: 查询结果
        """
        if not self._current_data_source:
            error("当前没有激活的数据源")
            return []
        
        data_source_type = self._current_data_source.get('type')
        
        try:
            if data_source_type == 'database':
                return self._execute_database_query(query, **kwargs)
            elif data_source_type == 'redis':
                return self._execute_redis_query(query, **kwargs)
            else:
                error(f"数据源类型 {data_source_type} 不支持查询操作")
                return []
                
        except Exception as e:
            error(f"执行查询失败: {e}")
            return []
    
    @contextmanager
    def temporary_switch(self, data_source_config: Union[str, Dict[str, Any]], **kwargs):
        """
        临时切换到指定数据源的上下文管理器
        :param data_source_config: 数据源配置
        :param kwargs: 其他参数
        """
        original_data_source = self._current_data_source
        
        try:
            # 切换到新数据源
            success = self.switch_to(data_source_config, **kwargs)
            if not success:
                raise Exception(f"无法切换到数据源: {data_source_config}")
            
            yield self
            
        finally:
            # 恢复原数据源
            if original_data_source:
                self.switch_to(original_data_source)
            else:
                self._current_data_source = None
    
    def get_switch_history(self) -> List[Dict[str, Any]]:
        """获取数据源切换历史"""
        return self._switch_history.copy()
    
    def clear_cache(self, cache_key: str = None):
        """清除缓存"""
        if cache_key:
            if cache_key in self._data_source_cache:
                del self._data_source_cache[cache_key]
                info(f"清除缓存: {cache_key}")
        else:
            self._data_source_cache.clear()
            info("清除所有缓存")
    
    def _parse_data_source_string(self, data_source_str: str) -> Dict[str, Any]:
        """解析数据源配置字符串"""
        if data_source_str.startswith('db://'):
            # 数据库数据源格式: db://type/env/sql?params
            return self._parse_database_string(data_source_str)
        elif data_source_str.startswith('redis://'):
            # Redis数据源格式: redis://env/key
            return self._parse_redis_string(data_source_str)
        elif data_source_str.startswith('file://'):
            # 文件数据源格式: file://path
            return self._parse_file_string(data_source_str)
        else:
            # 默认为文件路径
            return self._parse_file_string(f"file://{data_source_str}")
    
    def _parse_database_string(self, db_string: str) -> Dict[str, Any]:
        """解析数据库配置字符串"""
        # 格式: db://type/env/sql?param1=value1&param2=value2
        try:
            # 移除 db:// 前缀
            config_part = db_string[6:]
            
            # 分离查询参数
            if '?' in config_part:
                main_part, params_part = config_part.split('?', 1)
                params = dict(item.split('=') for item in params_part.split('&'))
            else:
                main_part = config_part
                params = {}
            
            # 解析主要部分 - 使用更智能的分割方式
            # 先按第一个 '/' 分割获取数据库类型和环境
            first_split = main_part.split('/', 1)
            if len(first_split) < 2:
                raise ValueError("数据库配置格式错误：缺少环境信息")
            
            db_type = first_split[0]
            remaining = first_split[1]
            
            # 从剩余部分中提取环境（通常是第一个部分）
            if '/' in remaining:
                env_part, sql_part = remaining.split('/', 1)
                env = env_part
                sql = sql_part
            else:
                # 如果没有更多 '/'，说明没有SQL部分
                env = remaining
                sql = ""
            
            # 修复数据库类型名称（处理可能的拼写错误）
            if db_type == 'ysql':
                db_type = 'mysql'
            
            return {
                'type': 'database',
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
        # 格式: redis://env/key
        try:
            config_part = redis_string[8:]  # 移除 redis:// 前缀
            parts = config_part.split('/', 1)
            
            if len(parts) < 2:
                raise ValueError("Redis配置格式错误")
            
            env, key = parts[0], parts[1]
            
            return {
                'type': 'redis',
                'env': env,
                'key': key,
                'name': f"redis_{env}"
            }
            
        except Exception as e:
            error(f"解析Redis配置字符串失败: {e}")
            return {}
    
    def _parse_file_string(self, file_string: str) -> Dict[str, Any]:
        """解析文件配置字符串"""
        # 格式: file://path
        try:
            path = file_string[7:] if file_string.startswith('file://') else file_string
            
            return {
                'type': 'file',
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
        
        if data_source_type == 'database':
            required_fields = ['db_type', 'env', 'sql']
        elif data_source_type == 'redis':
            required_fields = ['env', 'key']
        elif data_source_type == 'file':
            required_fields = ['path']
        else:
            error(f"不支持的数据源类型: {data_source_type}")
            return False
        
        for field in required_fields:
            if field not in config:
                error(f"数据源配置缺少必需字段: {field}")
                return False
        
        return True
    
    def _get_file_data(self, file_path: str) -> List[Dict[str, Any]]:
        """从文件获取数据"""
        cache_key = f"file_{file_path}"
        
        if cache_key in self._data_source_cache:
            return self._data_source_cache[cache_key]
        
        try:
            data = read_test_data(file_path)
            self._data_source_cache[cache_key] = data
            info(f"从文件加载数据: {file_path} ({len(data)} 条)")
            return data
        except Exception as e:
            error(f"从文件加载数据失败: {e}")
            return []
    
    def _get_database_data(self, sql: str) -> List[Dict[str, Any]]:
        """从数据库获取数据"""
        config = self._current_data_source
        cache_key = config.get('cache_key')
        
        if cache_key and cache_key in self._data_source_cache:
            return self._data_source_cache[cache_key]
        
        try:
            data = get_test_data_from_db(
                sql=sql,
                db_type=config['db_type'],
                env=config['env'],
                cache_key=cache_key
            )
            
            if cache_key:
                self._data_source_cache[cache_key] = data
            
            info(f"从数据库加载数据: {config['db_type']} - {config['env']} ({len(data)} 条)")
            return data
            
        except Exception as e:
            error(f"从数据库加载数据失败: {e}")
            return []
    
    def _get_redis_data(self, key: str) -> List[Dict[str, Any]]:
        """从Redis获取数据"""
        config = self._current_data_source
        cache_key = f"redis_{config['env']}_{key}"
        
        if cache_key in self._data_source_cache:
            return self._data_source_cache[cache_key]
        
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
            
            self._data_source_cache[cache_key] = data
            info(f"从Redis加载数据: {config['env']} - {key} ({len(data)} 条)")
            return data
            
        except Exception as e:
            error(f"从Redis加载数据失败: {e}")
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
    
    def _execute_database_query(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """执行数据库查询"""
        config = self._current_data_source
        
        try:
            return get_db_data(
                sql=query,
                db_type=config['db_type'],
                env=config['env'],
                params=kwargs.get('params')
            )
        except Exception as e:
            error(f"执行数据库查询失败: {e}")
            return []
    
    def _execute_redis_query(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """执行Redis查询"""
        config = self._current_data_source
        
        try:
            # Redis查询通常是键值操作
            if query.startswith('GET '):
                key = query[4:].strip()
                value = get_redis_value(key, config['env'])
                return [{'key': key, 'value': value}]
            elif query.startswith('SET '):
                # 格式: SET key value
                parts = query[4:].strip().split(' ', 1)
                if len(parts) >= 2:
                    key, value = parts[0], parts[1]
                    success = set_redis_value(key, value, config['env'])
                    return [{'key': key, 'value': value, 'success': success}]
            else:
                error(f"不支持的Redis查询格式: {query}")
                return []
                
        except Exception as e:
            error(f"执行Redis查询失败: {e}")
            return []
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 全局数据源切换器实例
data_source_switcher = DynamicDataSourceSwitcher()


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
            success = data_source_switcher.switch_to(data_source_config, **kwargs)
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
    return data_source_switcher.temporary_switch(data_source_config, **kwargs)


# 便捷函数
def get_current_data_source():
    """获取当前数据源配置"""
    return data_source_switcher.get_current_data_source()


def get_data_from_current_source(query: str = None, **kwargs):
    """从当前数据源获取数据"""
    return data_source_switcher.get_data(query, **kwargs)


def execute_query_on_current_source(query: str, **kwargs):
    """在当前数据源上执行查询"""
    return data_source_switcher.execute_query(query, **kwargs) 