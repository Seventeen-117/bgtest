# coding: utf-8
# @Author: bgtech
import os
import sys
import glob
import json
import configparser
import pandas as pd
from typing import Dict, List, Any, Optional, Union

# 尝试导入yaml，如果不可用则提供替代方案
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("警告: PyYAML未安装，YAML文件将无法读取")

# 导入数据源管理器
from common.data_source import get_test_data_from_db, get_db_data
from common.log import info, error, api_info, api_error

class ConfigManager:
    """
    统一配置管理器
    整合了interface_config、yaml_utils、interface_chain和get_caseparams的功能
    """
    
    def __init__(self, config_files: Optional[List[str]] = None):
        """
        初始化配置管理器
        :param config_files: 配置文件路径列表，支持yaml、ini、json格式
        """
        if config_files is None:
            # 自动检索 conf 目录下所有支持的配置文件
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            conf_dir = os.path.join(base_dir, 'conf')
            config_files = []
            for ext in ('*.yaml', '*.yml', '*.ini', '*.json'):
                config_files.extend(glob.glob(os.path.join(conf_dir, ext)))
        
        self.config_files = config_files
        self.interface_config = {}
        self.env_config = {}
        self.database_config = {}
        self.context = {}  # 存储接口返回值的上下文
        self._load_all_configs()
    
    # ==================== YAML处理功能 ====================
    
    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        加载YAML文件
        :param file_path: YAML文件路径
        :return: 解析后的字典数据
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"YAML文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return self._safe_yaml_load(file)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML文件解析错误: {e}")
        except Exception as e:
            raise Exception(f"读取YAML文件失败: {e}")
    
    def _safe_yaml_load(self, file):
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
    
    def save_yaml(self, data: Dict[str, Any], file_path: str, default_flow_style: bool = False) -> None:
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
    
    def merge_yaml(self, yaml1: Dict[str, Any], yaml2: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并两个YAML字典
        :param yaml1: 第一个YAML字典
        :param yaml2: 第二个YAML字典
        :return: 合并后的字典
        """
        result = yaml1.copy()
        for key, value in yaml2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_yaml(result[key], value)
            else:
                result[key] = value
        return result
    
    def validate_yaml_structure(self, data, required_keys):
        """
        校验Yaml对象是否包含所有必需key
        :param data: Yaml对象（dict）
        :param required_keys: 必需key列表
        :return: bool
        """
        return all(k in data for k in required_keys)
    
    # ==================== 配置文件加载功能 ====================
    
    def _load_all_configs(self):
        """加载所有配置文件（自动识别格式）"""
        for config_path in self.config_files:
            if os.path.exists(config_path):
                self._load_single_config(config_path)
            else:
                error(f"配置文件不存在: {config_path}")
    
    def _load_single_config(self, config_path: str):
        """加载单个配置文件"""
        try:
            if config_path.endswith(('.yaml', '.yml')):
                self._load_yaml_config(config_path)
            elif config_path.endswith('.ini'):
                self._load_ini_config(config_path)
            elif config_path.endswith('.json'):
                self._load_json_config(config_path)
            else:
                error(f"不支持的配置文件格式: {config_path}")
        except Exception as e:
            error(f"加载配置文件失败 {config_path}: {e}")
    
    def _load_yaml_config(self, config_path: str):
        config_data = self.load_yaml(config_path)
        if 'env' in config_data:
            self.env_config.update(config_data['env'])
        elif 'interfaces' in config_data:
            self._merge_interface_config(config_data)
        else:
            self._merge_config(self.interface_config, config_data)
    
    def _load_ini_config(self, config_path: str):
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        ini_dict = {}
        for section in config.sections():
            ini_dict[section] = dict(config[section])
        self._merge_config(self.interface_config, ini_dict)
    
    def _load_json_config(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        self._merge_config(self.interface_config, config_data)
    
    def _merge_interface_config(self, new_config: Dict):
        if 'interfaces' in new_config:
            if 'interfaces' not in self.interface_config:
                self.interface_config['interfaces'] = {}
            for module, interfaces in new_config['interfaces'].items():
                if module not in self.interface_config['interfaces']:
                    self.interface_config['interfaces'][module] = {}
                for interface, config in interfaces.items():
                    self.interface_config['interfaces'][module][interface] = config
        if 'global' in new_config:
            if 'global' not in self.interface_config:
                self.interface_config['global'] = {}
            self._merge_config(self.interface_config['global'], new_config['global'])
    
    def _merge_config(self, target: Dict, source: Dict):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value
    
    # ==================== 接口配置功能 ====================
    
    def get_current_env(self) -> str:
        return self.env_config.get('current', 'dev')
    
    def get_env_config(self, env: Optional[str] = None) -> Dict:
        if env is None:
            env = self.get_current_env()
        return self.env_config.get(env, {})
    
    def get_api_base_url(self, env: Optional[str] = None) -> str:
        env_config = self.get_env_config(env)
        url = env_config.get('api_base_url')
        if not url:
            raise ValueError("未在环境配置中找到 api_base_url，请检查配置文件。")
        return url
    
    def get_database_config(self, env: Optional[str] = None) -> Dict:
        env_config = self.get_env_config(env)
        return env_config.get('db', {})
    
    def get_interface_info(self, module: str, interface: str, env: Optional[str] = None) -> Dict:
        try:
            interface_info = self.interface_config['interfaces'][module][interface].copy()
            global_config = self.interface_config.get('global', {})
            if 'headers' not in interface_info:
                interface_info['headers'] = {}
            interface_info['headers'].update(global_config.get('default_headers', {}))
            if 'timeout' not in interface_info:
                interface_info['timeout'] = global_config.get('default_timeout', 30)
            if 'url' in interface_info:
                api_base_url = self.get_api_base_url(env)
                if interface_info['url'].startswith('${base_url}'):
                    interface_info['url'] = interface_info['url'].replace('${base_url}', api_base_url)
            return interface_info
        except KeyError as e:
            raise ValueError(f"接口配置不存在: {module}.{interface}")
        except Exception as e:
            raise Exception(f"获取接口配置失败: {e}")
    
    def get_all_interfaces(self) -> Dict:
        return self.interface_config.get('interfaces', {})
    
    def get_module_interfaces(self, module: str) -> Dict:
        try:
            return self.interface_config['interfaces'][module]
        except KeyError:
            raise ValueError(f"模块不存在: {module}")
    
    def get_global_config(self) -> Dict:
        return self.interface_config.get('global', {})
    
    def get_all_configs(self) -> Dict:
        return {
            'interface_config': self.interface_config,
            'env_config': self.env_config,
            'current_env': self.get_current_env()
        }
    
    # ==================== 测试数据加载功能 ====================
    
    def get_project_root(self):
        """获取项目根目录"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        return project_root
    
    def resolve_file_path(self, file_path):
        """解析文件路径，确保相对于项目根目录"""
        if os.path.isabs(file_path):
            return file_path
        
        project_root = self.get_project_root()
        absolute_path = os.path.join(project_root, file_path)
        
        if not os.path.exists(absolute_path):
            possible_paths = [
                absolute_path,
                os.path.join(os.getcwd(), file_path),
                file_path
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            
            return absolute_path
        
        return absolute_path
    
    def get_caseparams_dir(self):
        """获取caseparams目录的绝对路径"""
        project_root = self.get_project_root()
        caseparams_dir = os.path.join(project_root, 'caseparams')
        return caseparams_dir
    
    def get_supported_file_patterns(self):
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
    
    def load_all_caseparams_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载caseparams目录下所有支持格式的文件"""
        caseparams_dir = self.get_caseparams_dir()
        
        if not os.path.exists(caseparams_dir):
            error(f"caseparams目录不存在: {caseparams_dir}")
            return {}
        
        all_data = {}
        supported_patterns = self.get_supported_file_patterns()
        
        for pattern in supported_patterns:
            file_pattern = os.path.join(caseparams_dir, pattern)
            matching_files = glob.glob(file_pattern)
            
            for file_path in matching_files:
                try:
                    file_name = os.path.splitext(os.path.basename(file_path))[0]
                    data = self.read_test_data(file_path)
                    
                    if data:
                        all_data[file_name] = data
                        info(f"✓ 成功加载: {os.path.basename(file_path)} ({len(data)} 条数据)")
                    else:
                        info(f"⚠ 文件为空: {os.path.basename(file_path)}")
                        
                except Exception as e:
                    error(f"✗ 加载失败: {os.path.basename(file_path)} - {e}")
        
        return all_data
    
    def load_caseparams_by_type(self, file_type: str = None) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """根据文件类型加载caseparams文件"""
        caseparams_dir = self.get_caseparams_dir()
        
        if not os.path.exists(caseparams_dir):
            error(f"caseparams目录不存在: {caseparams_dir}")
            return {} if file_type is None else []
        
        if file_type is None:
            return self.load_all_caseparams_files()
        
        pattern = f"*.{file_type.lower()}"
        file_pattern = os.path.join(caseparams_dir, pattern)
        matching_files = glob.glob(file_pattern)
        
        all_data = []
        for file_path in matching_files:
            try:
                data = self.read_test_data(file_path)
                if data:
                    all_data.extend(data)
                    info(f"✓ 成功加载: {os.path.basename(file_path)} ({len(data)} 条数据)")
            except Exception as e:
                error(f"✗ 加载失败: {os.path.basename(file_path)} - {e}")
        
        return all_data
    
    def get_available_test_files(self) -> List[str]:
        """获取caseparams目录下所有可用的测试文件"""
        caseparams_dir = self.get_caseparams_dir()
        
        if not os.path.exists(caseparams_dir):
            return []
        
        available_files = []
        supported_patterns = self.get_supported_file_patterns()
        
        for pattern in supported_patterns:
            file_pattern = os.path.join(caseparams_dir, pattern)
            matching_files = glob.glob(file_pattern)
            available_files.extend(matching_files)
        
        return available_files
    
    def read_test_data(self, file_path, encoding='utf-8'):
        """读取测试数据文件"""
        # 检查是否是数据库查询配置
        if file_path.startswith('db://'):
            return self._read_test_data_from_db(file_path)
        
        # 解析文件路径
        resolved_path = self.resolve_file_path(file_path)
        
        ext = os.path.splitext(resolved_path)[-1].lower()
        try:
            if ext == '.xlsx':
                return pd.read_excel(resolved_path).to_dict(orient='records')
            elif ext in ('.yaml', '.yml'):
                if not YAML_AVAILABLE:
                    raise ImportError(f"PyYAML is required to read {resolved_path}. Please install it with: pip install PyYAML")
                return self.load_yaml(resolved_path)
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
    
    def _read_test_data_from_db(self, db_config: str) -> List[Dict[str, Any]]:
        """从数据库读取测试数据"""
        try:
            config_parts = db_config.replace('db://', '').split('/')
            if len(config_parts) < 3:
                raise ValueError("数据库配置格式错误，应为: db://db_type/env/sql")
            
            db_type = config_parts[0]
            env = config_parts[1]
            sql_part = '/'.join(config_parts[2:])
            
            if '?' in sql_part:
                sql, params_str = sql_part.split('?', 1)
                params = {}
                for param in params_str.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = value
            else:
                sql = sql_part
                params = {}
            
            cache_key = params.pop('cache_key', None)
            return get_test_data_from_db(sql, db_type, env, cache_key)
            
        except Exception as e:
            error(f"从数据库读取测试数据失败: {e}")
            return []
    
    # ==================== 接口链功能 ====================
    
    def extract_param(self, response, extract_rule):
        """从接口响应中提取参数"""
        try:
            if isinstance(extract_rule, str):
                keys = extract_rule.split('.')
                value = response
                for key in keys:
                    value = value.get(key)
                return value
            elif isinstance(extract_rule, dict):
                result = {}
                for param_name, rule in extract_rule.items():
                    keys = rule.split('.')
                    value = response
                    for key in keys:
                        value = value.get(key)
                    result[param_name] = value
                return result
        except Exception as e:
            api_error(f"参数提取失败: {e}")
            return None
    
    def replace_params(self, params, context):
        """替换参数中的占位符"""
        if isinstance(params, str):
            for key, value in context.items():
                placeholder = f"${{{key}}}"
                if placeholder in params:
                    params = params.replace(placeholder, str(value))
            return params
        elif isinstance(params, dict):
            result = {}
            for k, v in params.items():
                result[k] = self.replace_params(v, context)
            return result
        elif isinstance(params, list):
            return [self.replace_params(item, context) for item in params]
        else:
            return params
    
    def chain_request(self, interface_chain_data):
        """链式调用接口"""
        from utils.http_utils import http_get, http_post
        
        for step in interface_chain_data:
            try:
                url = step['url']
                method = step['method'].upper()
                params = step.get('params', {})
                
                if self.context:
                    params = self.replace_params(params, self.context)
                
                api_info(f"执行接口链步骤: {step.get('name', 'unnamed')}")
                api_info(f"请求地址: {url}")
                api_info(f"请求参数: {params}")
                
                if method == 'GET':
                    response = http_get(url, params=params)
                elif method == 'POST':
                    response = http_post(url, json_data=params)
                else:
                    raise ValueError(f"不支持的请求方法: {method}")
                
                api_info(f"接口响应: {response}")
                
                if 'extract' in step:
                    extracted = self.extract_param(response, step['extract'])
                    if extracted:
                        self.context.update(extracted)
                        api_info(f"提取参数: {extracted}")
                
                if 'assert' in step:
                    self.assert_response(response, step['assert'])
                
            except Exception as e:
                api_error(f"接口链执行失败: {e}")
                raise
        
        return response
    
    def assert_response(self, response, expected):
        """断言验证接口响应"""
        for key, expected_value in expected.items():
            actual_value = response.get(key)
            assert actual_value == expected_value, \
                f"断言失败: {key} 期望 {expected_value}, 实际 {actual_value}"
            api_info(f"断言通过: {key} = {actual_value}")
    
    # ==================== 便捷函数 ====================
    
    def get_all_test_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有测试数据的便捷函数"""
        return self.load_all_caseparams_files()
    
    def get_csv_test_data(self) -> List[Dict[str, Any]]:
        """获取所有CSV测试数据的便捷函数"""
        return self.load_caseparams_by_type('csv')
    
    def get_yaml_test_data(self) -> List[Dict[str, Any]]:
        """获取所有YAML测试数据的便捷函数"""
        return self.load_caseparams_by_type('yaml')
    
    def get_json_test_data(self) -> List[Dict[str, Any]]:
        """获取所有JSON测试数据的便捷函数"""
        return self.load_caseparams_by_type('json')
    
    def get_excel_test_data(self) -> List[Dict[str, Any]]:
        """获取所有Excel测试数据的便捷函数"""
        return self.load_caseparams_by_type('xlsx')

# 全局配置管理器实例
config_manager = ConfigManager()

# ==================== 便捷函数 ====================

def load_yaml(file_path: str) -> Dict[str, Any]:
    """加载YAML文件"""
    return config_manager.load_yaml(file_path)

def save_yaml(data: Dict[str, Any], file_path: str, default_flow_style: bool = False) -> None:
    """保存数据到YAML文件"""
    return config_manager.save_yaml(data, file_path, default_flow_style)

def merge_yaml(yaml1: Dict[str, Any], yaml2: Dict[str, Any]) -> Dict[str, Any]:
    """合并两个YAML字典"""
    return config_manager.merge_yaml(yaml1, yaml2)

def validate_yaml_structure(data, required_keys):
    """校验Yaml对象是否包含所有必需key"""
    return config_manager.validate_yaml_structure(data, required_keys)

def get_interface_config(module: str, interface: str, env: Optional[str] = None) -> Dict:
    """获取接口配置"""
    return config_manager.get_interface_info(module, interface, env)

def get_env_config(env: Optional[str] = None) -> Dict:
    """获取环境配置"""
    return config_manager.get_env_config(env)

def read_test_data(file_path, encoding='utf-8'):
    """读取测试数据文件"""
    return config_manager.read_test_data(file_path, encoding)

def get_all_test_data() -> Dict[str, List[Dict[str, Any]]]:
    """获取所有测试数据"""
    return config_manager.get_all_test_data()

def run_interface_chain(chain_config):
    """运行接口链"""
    return config_manager.chain_request(chain_config)

# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("统一配置管理器测试")
    print("=" * 60)
    
    # 测试配置加载
    current_env = config_manager.get_current_env()
    print(f"当前环境: {current_env}")
    
    # 测试测试数据加载
    try:
        all_data = get_all_test_data()
        print(f"加载了 {len(all_data)} 个测试数据文件")
    except Exception as e:
        print(f"测试数据加载失败: {e}")
    
    print("\n✓ 统一配置管理器测试完成！") 