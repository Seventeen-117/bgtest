# coding: utf-8
# @Author: bgtech
"""
统一数据驱动测试框架
整合文件数据、数据库数据和动态生成三种方式
支持pytest_generate_tests钩子实现动态测试生成
"""

import os
import sys
import json
import yaml
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from pathlib import Path
from functools import wraps
import pytest
import allure

# 导入项目模块
from common.get_caseparams import read_test_data, get_caseparams_dir
from common.data_source import get_test_data_from_db, get_db_data, get_redis_value, set_redis_value
from common.log import info, error, debug
from utils.http_utils import http_get, http_post, http_put, http_delete


class DataDrivenFramework:
    """统一数据驱动测试框架"""
    
    def __init__(self):
        self._test_data_cache = {}
        self._dynamic_generators = {}
        self._data_processors = {}
        
    def register_data_processor(self, data_type: str, processor: Callable):
        """
        注册数据处理器
        :param data_type: 数据类型
        :param processor: 处理函数
        """
        self._data_processors[data_type] = processor
        info(f"注册数据处理器: {data_type}")
    
    def register_dynamic_generator(self, name: str, generator: Callable):
        """
        注册动态数据生成器
        :param name: 生成器名称
        :param generator: 生成函数
        """
        self._dynamic_generators[name] = generator
        info(f"注册动态生成器: {name}")
    
    def load_test_data(self, source: Union[str, Dict], data_type: str = 'auto') -> List[Dict[str, Any]]:
        """
        统一加载测试数据
        :param source: 数据源（文件路径、数据库配置、字典等）
        :param data_type: 数据类型（auto, file, database, redis, dynamic）
        :return: 测试数据列表
        """
        if data_type == 'auto':
            data_type = self._detect_data_type(source)
        
        if data_type == 'file':
            return self._load_file_data(source)
        elif data_type == 'database':
            return self._load_database_data(source)
        elif data_type == 'redis':
            return self._load_redis_data(source)
        elif data_type == 'dynamic':
            return self._load_dynamic_data(source)
        elif data_type == 'mixed':
            return self._load_mixed_data(source)
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
    
    def _detect_data_type(self, source: Union[str, Dict]) -> str:
        """自动检测数据类型"""
        if isinstance(source, dict):
            return 'dynamic'
        elif isinstance(source, str):
            if source.startswith('db://'):
                return 'database'
            elif source.startswith('redis://'):
                return 'redis'
            elif source.startswith('dynamic://'):
                return 'dynamic'
            elif os.path.exists(source) or source.endswith(('.yaml', '.yml', '.json', '.csv', '.xlsx')):
                return 'file'
            else:
                return 'dynamic'
        else:
            return 'dynamic'
    
    def _load_file_data(self, file_path: str) -> List[Dict[str, Any]]:
        """加载文件数据"""
        try:
            data = read_test_data(file_path)
            info(f"从文件加载数据: {file_path} ({len(data)} 条)")
            return data
        except Exception as e:
            error(f"加载文件数据失败: {file_path} - {e}")
            return []
    
    def _load_database_data(self, db_config: str) -> List[Dict[str, Any]]:
        """加载数据库数据"""
        try:
            if db_config.startswith('db://'):
                data = read_test_data(db_config)
            else:
                # 假设是SQL字符串
                data = get_test_data_from_db(db_config, 'mysql', 'test')
            
            info(f"从数据库加载数据: {len(data)} 条")
            return data
        except Exception as e:
            error(f"加载数据库数据失败: {e}")
            return []
    
    def _load_redis_data(self, redis_key: str) -> List[Dict[str, Any]]:
        """加载Redis数据"""
        try:
            if redis_key.startswith('redis://'):
                key = redis_key.replace('redis://', '')
            else:
                key = redis_key
            
            data = get_redis_value(key, env='test')
            if isinstance(data, str):
                data = json.loads(data)
            
            if not isinstance(data, list):
                data = [data]
            
            info(f"从Redis加载数据: {key} ({len(data)} 条)")
            return data
        except Exception as e:
            error(f"加载Redis数据失败: {e}")
            return []
    
    def _load_dynamic_data(self, generator_config: Union[str, Dict]) -> List[Dict[str, Any]]:
        """加载动态生成数据"""
        try:
            if isinstance(generator_config, str):
                if generator_config.startswith('dynamic://'):
                    generator_name = generator_config.replace('dynamic://', '')
                else:
                    generator_name = generator_config
                
                if generator_name in self._dynamic_generators:
                    data = self._dynamic_generators[generator_name]()
                else:
                    error(f"未找到动态生成器: {generator_name}")
                    return []
            else:
                # 字典配置
                generator_name = generator_config.get('generator')
                params = generator_config.get('params', {})
                
                if generator_name in self._dynamic_generators:
                    data = self._dynamic_generators[generator_name](**params)
                else:
                    error(f"未找到动态生成器: {generator_name}")
                    return []
            
            info(f"动态生成数据: {len(data)} 条")
            return data
        except Exception as e:
            error(f"动态生成数据失败: {e}")
            return []
    
    def _load_mixed_data(self, mixed_config: Dict) -> List[Dict[str, Any]]:
        """加载混合数据"""
        try:
            combined_data = []
            
            # 加载基础数据
            base_source = mixed_config.get('base')
            if base_source:
                base_data = self.load_test_data(base_source)
                combined_data.extend(base_data)
            
            # 加载动态数据
            dynamic_source = mixed_config.get('dynamic')
            if dynamic_source:
                dynamic_data = self.load_test_data(dynamic_source)
                combined_data.extend(dynamic_data)
            
            # 合并数据
            if mixed_config.get('merge_strategy') == 'cross_product':
                # 笛卡尔积合并
                combined_data = self._cross_product_merge(base_data, dynamic_data)
            
            info(f"混合数据加载完成: {len(combined_data)} 条")
            return combined_data
        except Exception as e:
            error(f"加载混合数据失败: {e}")
            return []
    
    def _cross_product_merge(self, data1: List[Dict], data2: List[Dict]) -> List[Dict]:
        """笛卡尔积合并数据"""
        merged_data = []
        for item1 in data1:
            for item2 in data2:
                merged_item = item1.copy()
                merged_item.update(item2)
                merged_data.append(merged_item)
        return merged_data
    
    def process_test_data(self, data: List[Dict[str, Any]], processor_name: str = None) -> List[Dict[str, Any]]:
        """
        处理测试数据
        :param data: 原始数据
        :param processor_name: 处理器名称
        :return: 处理后的数据
        """
        if processor_name and processor_name in self._data_processors:
            return self._data_processors[processor_name](data)
        return data
    
    def generate_test_cases(self, test_data: List[Dict[str, Any]], 
                          test_function: Callable = None,
                          test_name_template: str = "test_{case_id}") -> List[Tuple[str, Dict[str, Any]]]:
        """
        生成测试用例
        :param test_data: 测试数据
        :param test_function: 测试函数
        :param test_name_template: 测试名称模板
        :return: 测试用例列表 [(test_name, test_data), ...]
        """
        test_cases = []
        
        for i, data in enumerate(test_data):
            case_id = data.get('case_id', f"case_{i+1}")
            test_name = test_name_template.format(case_id=case_id)
            test_cases.append((test_name, data))
        
        return test_cases


# 全局框架实例
data_driven_framework = DataDrivenFramework()


# ==================== 装饰器和工具函数 ====================

def data_driven(source: Union[str, Dict], data_type: str = 'auto', 
                processor: str = None, **kwargs):
    """
    数据驱动装饰器
    :param source: 数据源
    :param data_type: 数据类型
    :param processor: 数据处理器名称
    :param kwargs: 其他参数
    """
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **func_kwargs):
            # 加载测试数据
            test_data = data_driven_framework.load_test_data(source, data_type)
            
            # 处理数据
            if processor:
                test_data = data_driven_framework.process_test_data(test_data, processor)
            
            # 执行测试
            for data in test_data:
                # 移除pytest传递的test_data参数，使用我们加载的数据
                if 'test_data' in func_kwargs:
                    del func_kwargs['test_data']
                test_func(*args, test_data=data, **func_kwargs)
        
        return wrapper
    return decorator


def parametrize_from_source(source: Union[str, Dict], data_type: str = 'auto',
                           processor: str = None, **kwargs):
    """
    从数据源参数化装饰器
    """
    def decorator(test_func):
        # 加载测试数据
        test_data = data_driven_framework.load_test_data(source, data_type)
        
        # 处理数据
        if processor:
            test_data = data_driven_framework.process_test_data(test_data, processor)
        
        # 使用pytest.mark.parametrize
        return pytest.mark.parametrize("test_data", test_data)(test_func)
    
    return decorator


# ==================== 内置数据处理器 ====================

def validate_test_data_processor(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """验证测试数据处理器"""
    validated_data = []
    
    for item in data:
        # 验证必需字段
        required_fields = ['case_id', 'url', 'method']
        missing_fields = [field for field in required_fields if field not in item]
        
        if missing_fields:
            error(f"测试数据缺少必需字段: {missing_fields}")
            continue
        
        # 添加默认值
        item.setdefault('params', {})
        item.setdefault('expected_result', {})
        item.setdefault('description', f"测试用例 {item['case_id']}")
        
        validated_data.append(item)
    
    return validated_data


def add_timestamp_processor(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """添加时间戳处理器"""
    import time
    
    for item in data:
        item['timestamp'] = int(time.time())
        item['created_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    return data


# ==================== 内置动态生成器 ====================

def generate_sequential_data(**params) -> List[Dict[str, Any]]:
    """生成顺序数据"""
    count = params.get('count', 10)
    base_url = params.get('base_url', 'https://api.example.com')
    method = params.get('method', 'GET')
    
    data = []
    for i in range(count):
        data.append({
            'case_id': f"seq_{i+1}",
            'description': f"顺序测试用例 {i+1}",
            'url': f"{base_url}/test/{i+1}",
            'method': method,
            'params': {'id': i+1},
            'expected_result': {'status': 'success'}
        })
    
    return data


def generate_random_data(**params) -> List[Dict[str, Any]]:
    """生成随机数据"""
    import random
    import string
    
    count = params.get('count', 5)
    base_url = params.get('base_url', 'https://api.example.com')
    
    data = []
    for i in range(count):
        # 生成随机字符串
        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        data.append({
            'case_id': f"random_{i+1}",
            'description': f"随机测试用例 {i+1}",
            'url': f"{base_url}/random/{random_str}",
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'params': {'random_id': random_str},
            'expected_result': {'status': 'success'}
        })
    
    return data


# ==================== pytest钩子函数 ====================

def pytest_generate_tests(metafunc):
    """
    pytest动态测试生成钩子
    支持从文件、数据库、Redis等数据源动态生成测试用例
    """
    # 检查是否有data_source标记
    if hasattr(metafunc.function, 'data_source'):
        source = metafunc.function.data_source
        data_type = getattr(metafunc.function, 'data_type', 'auto')
        processor = getattr(metafunc.function, 'processor', None)
        
        # 加载测试数据
        test_data = data_driven_framework.load_test_data(source, data_type)
        
        # 处理数据
        if processor:
            test_data = data_driven_framework.process_test_data(test_data, processor)
        
        # 生成参数化测试
        if 'test_data' in metafunc.fixturenames:
            metafunc.parametrize("test_data", test_data)
    
    # 检查是否有dynamic_source标记
    if hasattr(metafunc.function, 'dynamic_source'):
        generator_name = metafunc.function.dynamic_source
        params = getattr(metafunc.function, 'generator_params', {})
        
        if generator_name in data_driven_framework._dynamic_generators:
            test_data = data_driven_framework._dynamic_generators[generator_name](**params)
            
            if 'test_data' in metafunc.fixturenames:
                metafunc.parametrize("test_data", test_data)


# ==================== 初始化内置处理器和生成器 ====================

def initialize_framework():
    """初始化框架"""
    # 注册内置数据处理器
    data_driven_framework.register_data_processor('validate', validate_test_data_processor)
    data_driven_framework.register_data_processor('add_timestamp', add_timestamp_processor)
    
    # 注册内置动态生成器
    data_driven_framework.register_dynamic_generator('sequential', generate_sequential_data)
    data_driven_framework.register_dynamic_generator('random', generate_random_data)
    
    info("数据驱动测试框架初始化完成")


# 自动初始化
initialize_framework()


# ==================== 使用示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("数据驱动测试框架示例")
    print("=" * 60)
    
    # 示例1: 从文件加载数据
    print("\n1. 从文件加载数据:")
    file_data = data_driven_framework.load_test_data('caseparams/test_chat_gateway.yaml')
    print(f"   加载了 {len(file_data)} 条数据")
    
    # 示例2: 从数据库加载数据
    print("\n2. 从数据库加载数据:")
    db_data = data_driven_framework.load_test_data('db://mysql/test/SELECT * FROM test_cases LIMIT 5')
    print(f"   加载了 {len(db_data)} 条数据")
    
    # 示例3: 动态生成数据
    print("\n3. 动态生成数据:")
    dynamic_data = data_driven_framework.load_test_data('dynamic://sequential', 'dynamic')
    print(f"   生成了 {len(dynamic_data)} 条数据")
    
    # 示例4: 混合数据源
    print("\n4. 混合数据源:")
    mixed_config = {
        'base': 'caseparams/test_chat_gateway.yaml',
        'dynamic': 'dynamic://random',
        'merge_strategy': 'cross_product'
    }
    mixed_data = data_driven_framework.load_test_data(mixed_config, 'mixed')
    print(f"   生成了 {len(mixed_data)} 条混合数据")
    
    print("\n✓ 数据驱动测试框架示例完成！") 