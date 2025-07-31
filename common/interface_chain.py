import re
import json
from common.log import api_info, api_error

class InterfaceChain:
    """
    接口关联处理工具类
    支持上一个接口返回值作为下一个接口参数
    """
    
    def __init__(self):
        self.context = {}  # 存储接口返回值的上下文
    
    def extract_param(self, response, extract_rule):
        """
        从接口响应中提取参数
        :param response: 接口响应（字典）
        :param extract_rule: 提取规则，如 'data.token' 或 '{"token": "data.token"}'
        :return: 提取的参数值或字典
        """
        try:
            if isinstance(extract_rule, str):
                # 简单提取单个值
                keys = extract_rule.split('.')
                value = response
                for key in keys:
                    value = value.get(key)
                return value
            elif isinstance(extract_rule, dict):
                # 批量提取多个值
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
        """
        替换参数中的占位符
        :param params: 原始参数
        :param context: 上下文（包含提取的参数）
        :return: 替换后的参数
        """
        if isinstance(params, str):
            # 字符串参数替换
            for key, value in context.items():
                placeholder = f"${{{key}}}"
                if placeholder in params:
                    params = params.replace(placeholder, str(value))
            return params
        elif isinstance(params, dict):
            # 字典参数递归替换
            result = {}
            for k, v in params.items():
                result[k] = self.replace_params(v, context)
            return result
        elif isinstance(params, list):
            # 列表参数递归替换
            return [self.replace_params(item, context) for item in params]
        else:
            return params
    
    def chain_request(self, interface_chain_data):
        """
        链式调用接口
        :param interface_chain_data: 接口链配置数据
        :return: 最后一个接口的响应
        """
        from utils.http_utils import http_get, http_post
        
        for step in interface_chain_data:
            try:
                # 获取接口信息
                url = step['url']
                method = step['method'].upper()
                params = step.get('params', {})
                
                # 替换参数中的占位符
                if self.context:
                    params = self.replace_params(params, self.context)
                
                api_info(f"执行接口链步骤: {step.get('name', 'unnamed')}")
                api_info(f"请求地址: {url}")
                api_info(f"请求参数: {params}")
                
                # 发送请求
                if method == 'GET':
                    response = http_get(url, params=params)
                elif method == 'POST':
                    response = http_post(url, json_data=params)
                else:
                    raise ValueError(f"不支持的请求方法: {method}")
                
                api_info(f"接口响应: {response}")
                
                # 提取参数到上下文
                if 'extract' in step:
                    extracted = self.extract_param(response, step['extract'])
                    if extracted:
                        self.context.update(extracted)
                        api_info(f"提取参数: {extracted}")
                
                # 断言验证
                if 'assert' in step:
                    self.assert_response(response, step['assert'])
                
            except Exception as e:
                api_error(f"接口链执行失败: {e}")
                raise
        
        return response
    
    def assert_response(self, response, expected):
        """
        断言验证接口响应
        :param response: 实际响应
        :param expected: 期望结果
        """
        for key, expected_value in expected.items():
            actual_value = response.get(key)
            assert actual_value == expected_value, \
                f"断言失败: {key} 期望 {expected_value}, 实际 {actual_value}"
            api_info(f"断言通过: {key} = {actual_value}")

# 使用示例
def run_interface_chain(chain_config):
    """
    运行接口链
    :param chain_config: 接口链配置
    """
    chain = InterfaceChain()
    return chain.chain_request(chain_config) 