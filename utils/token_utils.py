# coding: utf-8
# @Author: bgtech
import requests

_token_cache = {}

def get_token(login_url, login_data, headers=None, cache_key='default'):
    """
    登录获取token，支持缓存，避免重复登录。
    """
    if cache_key in _token_cache:
        return _token_cache[cache_key]
    resp = requests.post(login_url, json=login_data, headers=headers)
    resp.raise_for_status()
    token = resp.json().get('token')  # 根据实际返回结构调整
    _token_cache[cache_key] = token
    return token