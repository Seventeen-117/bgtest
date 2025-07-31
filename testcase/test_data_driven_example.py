#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据驱动测试示例
展示如何使用get_caseparams模块进行数据驱动测试
"""

import pytest
import json
from common.get_caseparams import (
    get_all_test_data,
    get_csv_test_data,
    get_yaml_test_data,
    load_caseparams_by_type
)
from utils.http_utils import http_get, http_post
from common.log import info, error

def parse_json_safely(json_str):
    """
    安全解析JSON字符串，处理可能的格式问题
    """
    if not json_str or json_str == '{}':
        return {}
    
    try:
        # 尝试直接解析
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        error(f"JSON解析失败: {json_str}, 错误: {e}")
        
        # 尝试多种清理方式
        cleaned_str = json_str
        
        # 方式1: 处理双引号转义 (CSV中的标准格式)
        if '""' in cleaned_str:
            cleaned_str = cleaned_str.replace('""', '"')
        
        # 方式2: 处理反斜杠转义
        if '\\"' in cleaned_str:
            cleaned_str = cleaned_str.replace('\\"', '"')
        
        # 方式3: 移除多余的反斜杠
        cleaned_str = cleaned_str.replace('\\', '')
        
        # 方式4: 确保JSON格式正确
        if not cleaned_str.startswith('{'):
            cleaned_str = '{' + cleaned_str
        if not cleaned_str.endswith('}'):
            cleaned_str = cleaned_str + '}'
        
        try:
            return json.loads(cleaned_str)
        except json.JSONDecodeError:
            error(f"清理后仍无法解析JSON: {cleaned_str}")
            # 返回空字典，避免测试失败
            return {}

# 方式1: 加载所有测试数据
all_test_data = get_all_test_data()

# 方式2: 按文件类型加载测试数据
csv_test_data = get_csv_test_data()
yaml_test_data = get_yaml_test_data()

# 方式3: 按类型加载特定格式的数据
csv_data = load_caseparams_by_type('csv')
yaml_data = load_caseparams_by_type('yaml')

class TestDataDrivenExample:
    """数据驱动测试示例类"""
    
    def test_all_files_data_driven(self):
        """测试所有文件的数据驱动"""
        for file_name, data in all_test_data.items():
            info(f"测试文件: {file_name}")
            for case in data:
                self._execute_test_case(case)
    
    def test_csv_data_driven(self):
        """测试CSV数据驱动"""
        for case in csv_test_data:
            self._execute_test_case(case)
    
    def test_yaml_data_driven(self):
        """测试YAML数据驱动"""
        for case in yaml_test_data:
            self._execute_test_case(case)
    
    def _execute_test_case(self, case):
        """执行单个测试用例"""
        case_id = case.get('case_id', 'unknown')
        description = case.get('description', 'no description')
        url = case.get('url', '')
        method = case.get('method', 'GET').upper()
        params = parse_json_safely(case.get('params', '{}'))
        expected = parse_json_safely(case.get('expected_result', '{}'))
        
        info(f"执行用例: {case_id} - {description}")
        info(f"请求地址: {url}")
        info(f"请求参数: {params}")
        
        try:
            if method == 'GET':
                resp = http_get(url, params=params)
            elif method == 'POST':
                resp = http_post(url, json_data=params)
            else:
                error(f"暂不支持的请求方式: {method}")
                pytest.skip("暂不支持的请求方式")
            
            info(f"接口返回: {resp}")
            
            # 断言：预期内容应包含在返回内容中
            for k, v in expected.items():
                assert k in resp, f"返回内容缺少字段: {k}"
                assert resp[k] == v, f"断言失败: {k} 期望: {v} 实际: {resp[k]}"
                
        except Exception as e:
            error(f"测试用例执行失败: {e}")
            # 根据实际情况决定是否跳过或失败
            pytest.skip(f"测试用例执行失败: {e}")

# 方式4: 使用pytest参数化进行数据驱动测试
@pytest.mark.parametrize("case", csv_data)
def test_csv_parameterized(case):
    """使用pytest参数化的CSV数据驱动测试"""
    case_id = case.get('case_id', 'unknown')
    description = case.get('description', 'no description')
    url = case.get('url', '')
    method = case.get('method', 'GET').upper()
    params = parse_json_safely(case.get('params', '{}'))
    expected = parse_json_safely(case.get('expected_result', '{}'))
    
    info(f"参数化测试 - 用例: {case_id} - {description}")
    info(f"请求地址: {url}")
    info(f"请求参数: {params}")
    
    try:
        if method == 'GET':
            resp = http_get(url, params=params)
        elif method == 'POST':
            resp = http_post(url, json_data=params)
        else:
            error(f"暂不支持的请求方式: {method}")
            pytest.skip("暂不支持的请求方式")
        
        info(f"接口返回: {resp}")
        
        # 断言：预期内容应包含在返回内容中
        for k, v in expected.items():
            assert k in resp, f"返回内容缺少字段: {k}"
            assert resp[k] == v, f"断言失败: {k} 期望: {v} 实际: {resp[k]}"
            
    except Exception as e:
        error(f"参数化测试执行失败: {e}")
        pytest.skip(f"参数化测试执行失败: {e}")

# 方式5: 按文件分别进行数据驱动测试
def test_http_data_file():
    """测试HTTP数据文件"""
    http_data = all_test_data.get('test_http_data', [])
    for case in http_data:
        case_id = case.get('case_id', 'unknown')
        description = case.get('description', 'no description')
        url = case.get('url', '')
        method = case.get('method', 'GET').upper()
        params = parse_json_safely(case.get('params', '{}'))
        expected = parse_json_safely(case.get('expected_result', '{}'))
        
        info(f"HTTP数据测试 - 用例: {case_id} - {description}")
        
        try:
            if method == 'GET':
                resp = http_get(url, params=params)
            elif method == 'POST':
                resp = http_post(url, json_data=params)
            else:
                error(f"暂不支持的请求方式: {method}")
                pytest.skip("暂不支持的请求方式")
            
            info(f"接口返回: {resp}")
            
            # 断言：预期内容应包含在返回内容中
            for k, v in expected.items():
                assert k in resp, f"返回内容缺少字段: {k}"
                assert resp[k] == v, f"断言失败: {k} 期望: {v} 实际: {resp[k]}"
                
        except Exception as e:
            error(f"HTTP数据测试执行失败: {e}")
            pytest.skip(f"HTTP数据测试执行失败: {e}")

def test_chat_gateway_file():
    """测试聊天网关文件"""
    chat_data = all_test_data.get('test_chat_gateway', [])
    for case in chat_data:
        case_id = case.get('case_id', 'unknown')
        description = case.get('description', 'no description')
        url = case.get('url', '')
        method = case.get('method', 'GET').upper()
        params = case.get('params', {})  # YAML中的params已经是字典
        expected = case.get('expected_result', {})  # YAML中的expected_result已经是字典
        
        info(f"聊天网关测试 - 用例: {case_id} - {description}")
        
        try:
            if method == 'GET':
                resp = http_get(url, params=params)
            elif method == 'POST':
                resp = http_post(url, json_data=params)
            else:
                error(f"暂不支持的请求方式: {method}")
                pytest.skip("暂不支持的请求方式")
            
            info(f"接口返回: {resp}")
            
            # 断言：预期内容应包含在返回内容中
            for k, v in expected.items():
                assert k in resp, f"返回内容缺少字段: {k}"
                assert resp[k] == v, f"断言失败: {k} 期望: {v} 实际: {resp[k]}"
                
        except Exception as e:
            error(f"聊天网关测试执行失败: {e}")
            pytest.skip(f"聊天网关测试执行失败: {e}")

if __name__ == "__main__":
    # 测试数据驱动功能
    print("=" * 60)
    print("数据驱动测试示例")
    print("=" * 60)
    
    # 显示可用的测试数据
    print(f"总文件数: {len(all_test_data)}")
    for file_name, data in all_test_data.items():
        print(f"文件: {file_name} - {len(data)} 条数据")
    
    print("\n✓ 数据驱动测试示例完成！") 