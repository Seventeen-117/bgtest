# coding: utf-8
# @Author: bgtech
import pandas as pd
import json
import os
import sys
import glob
from typing import List, Dict, Any, Union

# 尝试导入yaml，如果不可用则提供替代方案
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("警告: PyYAML未安装，YAML文件将无法读取")

def safe_yaml_load(file):
    """安全的YAML加载函数，处理Python版本兼容性问题"""
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML is not installed")
    
    try:
        return yaml.safe_load(file)
    except AttributeError as e:
        if "Hashable" in str(e):
            # 修复Python 3.10+的collections.Hashable问题
            import collections.abc
            # 重新定义SafeLoader以使用collections.abc.Hashable
            class SafeLoader(yaml.SafeLoader):
                pass
            
            def construct_mapping(loader, node):
                return dict(loader.construct_pairs(node))
            
            SafeLoader.add_constructor(
                yaml.resolver.Resolver.DEFAULT_MAPPING_TAG,
                construct_mapping
            )
            
            # 重新加载文件
            file.seek(0)
            return yaml.load(file, Loader=SafeLoader)
        else:
            raise e

def get_project_root():
    """获取项目根目录"""
    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 项目根目录是当前文件的上级目录
    project_root = os.path.dirname(current_dir)
    return project_root

def resolve_file_path(file_path):
    """解析文件路径，确保相对于项目根目录"""
    # 如果已经是绝对路径，直接返回
    if os.path.isabs(file_path):
        return file_path
    
    # 获取项目根目录
    project_root = get_project_root()
    
    # 构建绝对路径
    absolute_path = os.path.join(project_root, file_path)
    
    # 检查文件是否存在
    if not os.path.exists(absolute_path):
        # 尝试不同的路径组合
        possible_paths = [
            absolute_path,
            os.path.join(os.getcwd(), file_path),
            file_path
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # 如果都找不到，返回原始路径（让调用者处理错误）
        return absolute_path
    
    return absolute_path

def get_caseparams_dir():
    """获取caseparams目录的绝对路径"""
    project_root = get_project_root()
    caseparams_dir = os.path.join(project_root, 'caseparams')
    return caseparams_dir

def get_supported_file_patterns():
    """获取支持的文件格式模式"""
    return [
        '*.csv',
        '*.xlsx',
        '*.xls',
        '*.yaml',
        '*.yml',
        '*.json',
        '*.tsv'
    ]

def load_all_caseparams_files() -> Dict[str, List[Dict[str, Any]]]:
    """
    加载caseparams目录下所有支持格式的文件
    :return: 字典，键为文件名（不含扩展名），值为测试数据列表
    """
    caseparams_dir = get_caseparams_dir()
    
    if not os.path.exists(caseparams_dir):
        print(f"警告: caseparams目录不存在: {caseparams_dir}")
        return {}
    
    all_data = {}
    supported_patterns = get_supported_file_patterns()
    
    for pattern in supported_patterns:
        # 使用glob查找匹配的文件
        file_pattern = os.path.join(caseparams_dir, pattern)
        matching_files = glob.glob(file_pattern)
        
        for file_path in matching_files:
            try:
                # 获取文件名（不含扩展名）作为键
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 读取文件数据
                data = read_test_data(file_path)
                
                if data:
                    all_data[file_name] = data
                    print(f"✓ 成功加载: {os.path.basename(file_path)} ({len(data)} 条数据)")
                else:
                    print(f"⚠ 文件为空: {os.path.basename(file_path)}")
                    
            except Exception as e:
                print(f"✗ 加载失败: {os.path.basename(file_path)} - {e}")
    
    return all_data

def load_caseparams_by_type(file_type: str = None) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    根据文件类型加载caseparams文件
    :param file_type: 文件类型（csv, yaml, json, xlsx等），如果为None则加载所有类型
    :return: 如果指定了file_type返回数据列表，否则返回所有数据的字典
    """
    caseparams_dir = get_caseparams_dir()
    
    if not os.path.exists(caseparams_dir):
        print(f"警告: caseparams目录不存在: {caseparams_dir}")
        return {} if file_type is None else []
    
    if file_type is None:
        # 加载所有类型的文件
        return load_all_caseparams_files()
    
    # 加载指定类型的文件
    pattern = f"*.{file_type.lower()}"
    file_pattern = os.path.join(caseparams_dir, pattern)
    matching_files = glob.glob(file_pattern)
    
    all_data = []
    for file_path in matching_files:
        try:
            data = read_test_data(file_path)
            if data:
                all_data.extend(data)
                print(f"✓ 成功加载: {os.path.basename(file_path)} ({len(data)} 条数据)")
        except Exception as e:
            print(f"✗ 加载失败: {os.path.basename(file_path)} - {e}")
    
    return all_data

def get_available_test_files() -> List[str]:
    """
    获取caseparams目录下所有可用的测试文件
    :return: 文件路径列表
    """
    caseparams_dir = get_caseparams_dir()
    
    if not os.path.exists(caseparams_dir):
        return []
    
    available_files = []
    supported_patterns = get_supported_file_patterns()
    
    for pattern in supported_patterns:
        file_pattern = os.path.join(caseparams_dir, pattern)
        matching_files = glob.glob(file_pattern)
        available_files.extend(matching_files)
    
    return available_files

def read_test_data(file_path, encoding='utf-8'):
    """
    读取测试数据文件
    :param file_path: 文件路径（相对于项目根目录或绝对路径）
    :param encoding: 文件编码
    :return: 数据列表
    """
    # 解析文件路径
    resolved_path = resolve_file_path(file_path)
    
    ext = os.path.splitext(resolved_path)[-1].lower()
    try:
        if ext == '.xlsx':
            return pd.read_excel(resolved_path).to_dict(orient='records')
        elif ext in ('.yaml', '.yml'):
            if not YAML_AVAILABLE:
                raise ImportError(f"PyYAML is required to read {resolved_path}. Please install it with: pip install PyYAML")
            with open(resolved_path, 'r', encoding=encoding) as file:
                return safe_yaml_load(file)
        elif ext == '.csv':
            return pd.read_csv(resolved_path, encoding=encoding).to_dict(orient='records')
        elif ext == '.tsv':
            return pd.read_csv(resolved_path, sep='\t', encoding=encoding).to_dict(orient='records')
        elif ext == '.json':
            with open(resolved_path, 'r', encoding=encoding) as file:
                return json.load(file)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        raise RuntimeError(f"Failed to read {resolved_path} with encoding {encoding}: {e}")

# 便捷函数
def get_all_test_data() -> Dict[str, List[Dict[str, Any]]]:
    """
    获取所有测试数据的便捷函数
    :return: 所有测试数据的字典
    """
    return load_all_caseparams_files()

def get_csv_test_data() -> List[Dict[str, Any]]:
    """
    获取所有CSV测试数据的便捷函数
    :return: CSV测试数据列表
    """
    return load_caseparams_by_type('csv')

def get_yaml_test_data() -> List[Dict[str, Any]]:
    """
    获取所有YAML测试数据的便捷函数
    :return: YAML测试数据列表
    """
    return load_caseparams_by_type('yaml')

def get_json_test_data() -> List[Dict[str, Any]]:
    """
    获取所有JSON测试数据的便捷函数
    :return: JSON测试数据列表
    """
    return load_caseparams_by_type('json')

def get_excel_test_data() -> List[Dict[str, Any]]:
    """
    获取所有Excel测试数据的便捷函数
    :return: Excel测试数据列表
    """
    return load_caseparams_by_type('xlsx')

# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("测试数据驱动功能")
    print("=" * 60)
    
    try:
        # 1. 获取所有可用的测试文件
        print("\n1. 可用的测试文件:")
        available_files = get_available_test_files()
        for file_path in available_files:
            print(f"   {os.path.basename(file_path)}")
        
        # 2. 加载所有测试数据
        print("\n2. 加载所有测试数据:")
        all_data = get_all_test_data()
        for file_name, data in all_data.items():
            print(f"   {file_name}: {len(data)} 条数据")
        
        # 3. 按类型加载测试数据
        print("\n3. 按类型加载测试数据:")
        
        csv_data = get_csv_test_data()
        print(f"   CSV数据: {len(csv_data)} 条")
        
        yaml_data = get_yaml_test_data()
        print(f"   YAML数据: {len(yaml_data)} 条")
        
        # 4. 测试单个文件读取
        print("\n4. 测试单个文件读取:")
        if available_files:
            test_file = available_files[0]
            data = read_test_data(test_file)
            print(f"   {os.path.basename(test_file)}: {len(data)} 条数据")
        
        print("\n✓ 数据驱动功能测试完成！")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()