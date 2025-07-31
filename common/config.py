# coding: utf-8
# @Author: bgtech
import os
import configparser
import yaml

global_config = {}

# 自动加载conf目录下所有yaml和ini配置文件
def load_all_configs(conf_dir=None):
    global global_config
    if conf_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        conf_dir = os.path.join(base_dir, 'conf')
    for fname in os.listdir(conf_dir):
        fpath = os.path.join(conf_dir, fname)
        if fname.endswith('.ini'):
            parser = configparser.ConfigParser()
            parser.read(fpath, encoding='utf-8')
            for section in parser.sections():
                if section not in global_config:
                    global_config[section] = {}
                for k, v in parser.items(section):
                    global_config[section][k] = v
        elif fname.endswith('.yaml') or fname.endswith('.yml'):
            with open(fpath, 'r', encoding='utf-8') as f:
                yml = yaml.safe_load(f)
                if yml:
                    global_config.update(yml)

def get_config(*keys, default=None):
    """
    支持多级嵌套key访问，如get_config('api', 'url.host')或get_config('api.url.host')。
    """
    if not keys:
        return global_config
    # 支持传入多个参数或用点分隔的字符串
    path = []
    for k in keys:
        if isinstance(k, str):
            path.extend(k.split('.'))
        elif isinstance(k, (list, tuple)):
            path.extend(k)
    val = global_config
    for k in path:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return default
    return val

# 项目启动时自动加载
def _auto_load():
    load_all_configs()

_auto_load()