# coding: utf-8
# @Author: bgtech
import pytest
from utils.token_utils import get_token

@pytest.fixture(scope='session', autouse=True)
def global_token():
    # 这里的url和data可以从配置文件读取
    login_url = 'http://example.com/api/login'
    login_data = {'username': 'user', 'password': 'pass'}
    token = get_token(login_url, login_data)
    return token

@pytest.fixture(autouse=True)
def inject_token(request, global_token):
    """
    自动为每个用例注入token到request上下文
    """
    request.cls.token = global_token