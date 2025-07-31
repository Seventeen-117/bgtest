#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON文件读取工具
支持加载、解析、读取JSON文件，包括多层嵌套结构
"""

import json
import os
import re
from typing import Any, Dict, List, Union, Optional, Tuple
from common.log import info, error, debug

class JSONFileReader:
    """JSON文件读取器，支持多层嵌套结构"""
    
    def __init__(self, file_path: str = None, encoding: str = 'utf-8'):
        """
        初始化JSON文件读取器
        :param file_path: JSON文件路径
        :param encoding: 文件编码
        """
        self.file_path = file_path
        self.encoding = encoding
        self.data = None
        self._loaded = False
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path: str) -> bool:
        """
        加载JSON文件
        :param file_path: JSON文件路径
        :return: 是否加载成功
        """
        try:
            self.file_path = file_path
            with open(file_path, 'r', encoding=self.encoding) as f:
                self.data = json.load(f)
            self._loaded = True
            info(f"成功加载JSON文件: {file_path}")
            return True
        except FileNotFoundError:
            error(f"文件不存在: {file_path}")
            return False
        except json.JSONDecodeError as e:
            error(f"JSON格式错误: {file_path}, 错误: {e}")
            return False
        except Exception as e:
            error(f"读取文件失败: {file_path}, 错误: {e}")
            return False
    
    def load_string(self, json_string: str) -> bool:
        """
        从字符串加载JSON数据
        :param json_string: JSON字符串
        :return: 是否加载成功
        """
        try:
            self.data = json.loads(json_string)
            self._loaded = True
            info("成功从字符串加载JSON数据")
            return True
        except json.JSONDecodeError as e:
            error(f"JSON字符串格式错误: {e}")
            return False
        except Exception as e:
            error(f"解析JSON字符串失败: {e}")
            return False
    
    def get_data(self) -> Any:
        """
        获取完整的JSON数据
        :return: JSON数据
        """
        if not self._loaded:
            error("JSON数据未加载")
            return None
        return self.data
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        根据路径获取JSON中的值，支持多层嵌套
        :param path: 路径，支持点号分隔和数组索引，如 "user.profile.name" 或 "users[0].name"
        :param default: 默认值
        :return: 找到的值或默认值
        """
        if not self._loaded:
            error("JSON数据未加载")
            return default
        
        try:
            return self._get_value_by_path(self.data, path, default)
        except Exception as e:
            error(f"获取路径 {path} 的值失败: {e}")
            return default
    
    def _get_value_by_path(self, data: Any, path: str, default: Any) -> Any:
        """
        根据路径获取值的内部方法
        :param data: 数据对象
        :param path: 路径
        :param default: 默认值
        :return: 找到的值或默认值
        """
        if not path:
            return data
        
        # 解析路径
        parts = self._parse_path(path)
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    return default
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        return default
                except (ValueError, IndexError):
                    return default
            else:
                return default
        
        return current
    
    def _parse_path(self, path: str) -> List[str]:
        """
        解析路径字符串
        :param path: 路径字符串，如 "user.profile.name" 或 "users[0].name"
        :return: 路径部分列表
        """
        parts = []
        current = ""
        in_bracket = False
        
        for char in path:
            if char == '[':
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = True
            elif char == ']':
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = False
            elif char == '.' and not in_bracket:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            parts.append(current)
        
        return parts
    
    def set_value(self, path: str, value: Any) -> bool:
        """
        设置JSON中的值
        :param path: 路径
        :param value: 要设置的值
        :return: 是否设置成功
        """
        if not self._loaded:
            error("JSON数据未加载")
            return False
        
        try:
            parts = self._parse_path(path)
            if not parts:
                self.data = value
                return True
            
            current = self.data
            for i, part in enumerate(parts[:-1]):
                if isinstance(current, dict):
                    if part not in current:
                        # 如果下一部分是数字，创建列表
                        if i + 1 < len(parts) and parts[i + 1].isdigit():
                            current[part] = []
                        else:
                            current[part] = {}
                    current = current[part]
                elif isinstance(current, list):
                    try:
                        index = int(part)
                        if index >= len(current):
                            current.extend([None] * (index - len(current) + 1))
                        current = current[index]
                    except (ValueError, IndexError):
                        return False
                else:
                    return False
            
            # 设置最终值
            last_part = parts[-1]
            if isinstance(current, dict):
                current[last_part] = value
            elif isinstance(current, list):
                try:
                    index = int(last_part)
                    if index >= len(current):
                        current.extend([None] * (index - len(current) + 1))
                    current[index] = value
                except (ValueError, IndexError):
                    return False
            else:
                return False
            
            info(f"成功设置路径 {path} 的值为: {value}")
            return True
            
        except Exception as e:
            error(f"设置路径 {path} 的值失败: {e}")
            return False
    
    def delete_value(self, path: str) -> bool:
        """
        删除JSON中的值
        :param path: 路径
        :return: 是否删除成功
        """
        if not self._loaded:
            error("JSON数据未加载")
            return False
        
        try:
            parts = self._parse_path(path)
            if not parts:
                return False
            
            current = self.data
            for i, part in enumerate(parts[:-1]):
                if isinstance(current, dict):
                    if part not in current:
                        return False
                    current = current[part]
                elif isinstance(current, list):
                    try:
                        index = int(part)
                        if 0 <= index < len(current):
                            current = current[index]
                        else:
                            return False
                    except (ValueError, IndexError):
                        return False
                else:
                    return False
            
            # 删除最终值
            last_part = parts[-1]
            if isinstance(current, dict):
                if last_part in current:
                    del current[last_part]
                    info(f"成功删除路径 {path}")
                    return True
            elif isinstance(current, list):
                try:
                    index = int(last_part)
                    if 0 <= index < len(current):
                        del current[index]
                        info(f"成功删除路径 {path}")
                        return True
                except (ValueError, IndexError):
                    pass
            
            return False
            
        except Exception as e:
            error(f"删除路径 {path} 的值失败: {e}")
            return False
    
    def search_values(self, key: str, max_depth: int = 10) -> List[Tuple[str, Any]]:
        """
        搜索JSON中指定键的所有值
        :param key: 要搜索的键
        :param max_depth: 最大搜索深度
        :return: 找到的路径和值的列表
        """
        if not self._loaded:
            error("JSON数据未加载")
            return []
        
        results = []
        self._search_recursive(self.data, key, "", results, max_depth, 0)
        return results
    
    def _search_recursive(self, data: Any, key: str, current_path: str, 
                         results: List[Tuple[str, Any]], max_depth: int, depth: int):
        """
        递归搜索值的内部方法
        """
        if depth > max_depth:
            return
        
        if isinstance(data, dict):
            for k, v in data.items():
                new_path = f"{current_path}.{k}" if current_path else k
                if k == key:
                    results.append((new_path, v))
                self._search_recursive(v, key, new_path, results, max_depth, depth + 1)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{current_path}[{i}]"
                self._search_recursive(item, key, new_path, results, max_depth, depth + 1)
    
    def get_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        获取JSON结构信息
        :param max_depth: 最大深度
        :return: 结构信息
        """
        if not self._loaded:
            error("JSON数据未加载")
            return {}
        
        return self._get_structure_recursive(self.data, max_depth, 0)
    
    def _get_structure_recursive(self, data: Any, max_depth: int, depth: int) -> Dict[str, Any]:
        """
        递归获取结构信息的内部方法
        """
        if depth > max_depth:
            return {"type": "..."}
        
        if isinstance(data, dict):
            structure = {"type": "dict", "keys": list(data.keys())}
            if depth < max_depth:
                structure["children"] = {
                    k: self._get_structure_recursive(v, max_depth, depth + 1)
                    for k, v in data.items()
                }
            return structure
        elif isinstance(data, list):
            structure = {"type": "list", "length": len(data)}
            if data and depth < max_depth:
                structure["sample"] = self._get_structure_recursive(data[0], max_depth, depth + 1)
            return structure
        else:
            return {"type": type(data).__name__, "value": str(data)[:50]}
    
    def save_file(self, file_path: str = None, indent: int = 2) -> bool:
        """
        保存JSON数据到文件
        :param file_path: 文件路径，如果为None则使用原文件路径
        :param indent: 缩进空格数
        :return: 是否保存成功
        """
        if not self._loaded:
            error("JSON数据未加载")
            return False
        
        try:
            save_path = file_path or self.file_path
            if not save_path:
                error("未指定保存路径")
                return False
            
            with open(save_path, 'w', encoding=self.encoding) as f:
                json.dump(self.data, f, indent=indent, ensure_ascii=False)
            
            info(f"成功保存JSON文件: {save_path}")
            return True
        except Exception as e:
            error(f"保存JSON文件失败: {e}")
            return False
    
    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证JSON数据是否符合指定的schema
        :param schema: 验证schema
        :return: (是否有效, 错误信息列表)
        """
        if not self._loaded:
            return False, ["JSON数据未加载"]
        
        errors = []
        self._validate_recursive(self.data, schema, "", errors)
        return len(errors) == 0, errors
    
    def _validate_recursive(self, data: Any, schema: Dict[str, Any], path: str, errors: List[str]):
        """
        递归验证数据的内部方法
        """
        if "type" not in schema:
            return
        
        expected_type = schema["type"]
        
        if expected_type == "object" and not isinstance(data, dict):
            errors.append(f"{path}: 期望对象类型，实际为 {type(data).__name__}")
            return
        elif expected_type == "array" and not isinstance(data, list):
            errors.append(f"{path}: 期望数组类型，实际为 {type(data).__name__}")
            return
        elif expected_type in ["string", "number", "boolean"]:
            if not isinstance(data, (str, int, float, bool)):
                errors.append(f"{path}: 期望 {expected_type} 类型，实际为 {type(data).__name__}")
                return
        
        if expected_type == "object" and isinstance(data, dict):
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    errors.append(f"{path}: 缺少必需字段 '{field}'")
            
            properties = schema.get("properties", {})
            for key, value in data.items():
                if key in properties:
                    new_path = f"{path}.{key}" if path else key
                    self._validate_recursive(value, properties[key], new_path, errors)
        
        elif expected_type == "array" and isinstance(data, list):
            items_schema = schema.get("items", {})
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]"
                self._validate_recursive(item, items_schema, new_path, errors)

# 便捷函数
def read_json_file(file_path: str, encoding: str = 'utf-8') -> Any:
    """
    读取JSON文件的便捷函数
    :param file_path: 文件路径
    :param encoding: 文件编码
    :return: JSON数据
    """
    reader = JSONFileReader(file_path, encoding)
    return reader.get_data()

def get_json_value(file_path: str, path: str, default: Any = None, encoding: str = 'utf-8') -> Any:
    """
    从JSON文件中获取指定路径的值的便捷函数
    :param file_path: 文件路径
    :param path: 路径
    :param default: 默认值
    :param encoding: 文件编码
    :return: 找到的值或默认值
    """
    reader = JSONFileReader(file_path, encoding)
    return reader.get_value(path, default)

def write_json_file(file_path: str, data: Any, indent: int = 2, encoding: str = 'utf-8') -> bool:
    """
    写入JSON文件的便捷函数
    :param file_path: 文件路径
    :param data: 要写入的数据
    :param indent: 缩进空格数
    :param encoding: 文件编码
    :return: 是否写入成功
    """
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        info(f"成功写入JSON文件: {file_path}")
        return True
    except Exception as e:
        error(f"写入JSON文件失败: {e}")
        return False

def merge_json_files(file_paths: List[str], output_path: str, encoding: str = 'utf-8') -> bool:
    """
    合并多个JSON文件
    :param file_paths: 要合并的文件路径列表
    :param output_path: 输出文件路径
    :param encoding: 文件编码
    :return: 是否合并成功
    """
    try:
        merged_data = {}
        for file_path in file_paths:
            reader = JSONFileReader(file_path, encoding)
            data = reader.get_data()
            if isinstance(data, dict):
                merged_data.update(data)
            else:
                error(f"文件 {file_path} 不是有效的JSON对象")
                return False
        
        return write_json_file(output_path, merged_data, encoding=encoding)
    except Exception as e:
        error(f"合并JSON文件失败: {e}")
        return False

# 使用示例
if __name__ == "__main__":
    # 创建示例JSON文件
    sample_data = {
        "user": {
            "id": 1,
            "name": "张三",
            "profile": {
                "age": 25,
                "email": "zhangsan@example.com",
                "addresses": [
                    {"type": "home", "city": "北京"},
                    {"type": "work", "city": "上海"}
                ]
            }
        },
        "settings": {
            "theme": "dark",
            "language": "zh-CN"
        }
    }
    
    # 写入示例文件
    write_json_file("sample.json", sample_data)
    
    # 测试JSON读取器
    reader = JSONFileReader("sample.json")
    
    print("=" * 60)
    print("JSON文件读取工具测试")
    print("=" * 60)
    
    # 1. 获取值
    print("\n1. 获取值测试:")
    print(f"用户名: {reader.get_value('user.name')}")
    print(f"年龄: {reader.get_value('user.profile.age')}")
    print(f"第一个地址: {reader.get_value('user.profile.addresses[0]')}")
    print(f"不存在的路径: {reader.get_value('user.notexist', '默认值')}")
    
    # 2. 设置值
    print("\n2. 设置值测试:")
    reader.set_value('user.profile.phone', '13800138000')
    print(f"设置后的电话: {reader.get_value('user.profile.phone')}")
    
    # 3. 搜索值
    print("\n3. 搜索值测试:")
    results = reader.search_values('city')
    for path, value in results:
        print(f"找到 {path}: {value}")
    
    # 4. 获取结构
    print("\n4. 获取结构测试:")
    structure = reader.get_structure()
    print(f"JSON结构: {structure}")
    
    # 5. 保存文件
    print("\n5. 保存文件测试:")
    reader.save_file("sample_updated.json")
    
    print("\n✓ JSON文件读取工具测试完成！") 