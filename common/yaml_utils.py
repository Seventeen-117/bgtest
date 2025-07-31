# coding: utf-8
# @Author: bgtech
import yaml
import os
from typing import Dict, Any, Optional

def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    加载YAML文件
    :param file_path: YAML文件路径
    :return: 解析后的字典数据
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML文件不存在: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML文件解析错误: {e}")
    except Exception as e:
        raise Exception(f"读取YAML文件失败: {e}")

def save_yaml(data: Dict[str, Any], file_path: str, default_flow_style: bool = False) -> None:
    """
    保存数据到YAML文件
    :param data: 要保存的数据
    :param file_path: 保存路径
    :param default_flow_style: 是否使用流式样式
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=default_flow_style, allow_unicode=True)
    except Exception as e:
        raise Exception(f"保存YAML文件失败: {e}")

def merge_yaml(yaml1: Dict[str, Any], yaml2: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个YAML字典
    :param yaml1: 第一个YAML字典
    :param yaml2: 第二个YAML字典
    :return: 合并后的字典
    """
    result = yaml1.copy()
    for key, value in yaml2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_yaml(result[key], value)
        else:
            result[key] = value
    return result

def validate_yaml_structure(data, required_keys):
    """
    校验Yaml对象是否包含所有必需key
    :param data: Yaml对象（dict）
    :param required_keys: 必需key列表
    :return: bool
    """
    return all(k in data for k in required_keys) 