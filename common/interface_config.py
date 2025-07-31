from common.yaml_utils import load_yaml
from common.config import get_config
import os
import configparser
import glob
import json
from typing import Dict, List, Any, Optional

class InterfaceConfig:
    """
    接口配置管理工具
    用于读取和管理接口基本信息，支持多配置文件自动加载（ini/yaml/json）
    """
    
    def __init__(self, config_files: Optional[List[str]] = None):
        """
        初始化接口配置
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
        self._load_all_configs()

    def _load_all_configs(self):
        """
        加载所有配置文件（自动识别格式）
        """
        for config_path in self.config_files:
            if os.path.exists(config_path):
                self._load_single_config(config_path)
            else:
                print(f"警告: 配置文件不存在: {config_path}")

    def _load_single_config(self, config_path: str):
        """
        加载单个配置文件
        :param config_path: 配置文件路径
        """
        try:
            if config_path.endswith(('.yaml', '.yml')):
                self._load_yaml_config(config_path)
            elif config_path.endswith('.ini'):
                self._load_ini_config(config_path)
            elif config_path.endswith('.json'):
                self._load_json_config(config_path)
            else:
                print(f"警告: 不支持的配置文件格式: {config_path}")
        except Exception as e:
            print(f"加载配置文件失败 {config_path}: {e}")

    def _load_yaml_config(self, config_path: str):
        config_data = load_yaml(config_path)
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
            raise ValueError("未在环境配置中找到 api_base_url，请检查配置文件。");
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
                # 用占位符替换，不再硬编码
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

# 便捷函数

def get_interface_config(module: str, interface: str, env: Optional[str] = None) -> Dict:
    config = InterfaceConfig()
    return config.get_interface_info(module, interface, env)

def get_env_config(env: Optional[str] = None) -> Dict:
    config = InterfaceConfig()
    return config.get_env_config(env)

# 示例用法
if __name__ == "__main__":
    config = InterfaceConfig()
    current_env = config.get_current_env()
    print(f"当前环境: {current_env}")
    env_config = config.get_env_config()
    print(f"环境配置: {env_config}")
    api_base_url = config.get_api_base_url()
    print(f"API基础URL: {api_base_url}")
    login_config = get_interface_config('user', 'login')
    print(f"登录接口配置: {login_config}")
    all_interfaces = config.get_all_interfaces()
    print(f"所有接口模块: {list(all_interfaces.keys())}")
    all_configs = config.get_all_configs()
    print(f"所有配置信息: {all_configs}") 