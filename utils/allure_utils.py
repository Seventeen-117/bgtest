# coding: utf-8
# @Author: bgtech
import allure
import json
import time
import traceback
from typing import Dict, Any, Optional, Union
from allure_commons.types import AttachmentType
from functools import wraps
import requests
from common.log import info, error, debug

class AllureUtils:
    """Allure报告增强工具类"""
    
    def __init__(self):
        self.test_start_time = None
        self.test_end_time = None
    
    @staticmethod
    def step(step_title: str):
        """
        Allure步骤装饰器
        :param step_title: 步骤标题
        """
        return allure.step(step_title)
    
    @staticmethod
    def attach_text(content: str, name: str = "Text Attachment"):
        """
        附加文本内容到Allure报告
        :param content: 文本内容
        :param name: 附件名称
        """
        allure.attach(
            content,
            name=name,
            attachment_type=AttachmentType.TEXT
        )
    
    @staticmethod
    def attach_json(data: Dict[str, Any], name: str = "JSON Data"):
        """
        附加JSON数据到Allure报告
        :param data: JSON数据
        :param name: 附件名称
        """
        allure.attach(
            json.dumps(data, ensure_ascii=False, indent=2),
            name=name,
            attachment_type=AttachmentType.JSON
        )
    
    @staticmethod
    def attach_request_details(method: str, url: str, headers: Dict = None, 
                             params: Dict = None, data: Dict = None, 
                             json_data: Dict = None, name: str = "Request Details"):
        """
        附加请求详细信息到Allure报告
        :param method: HTTP方法
        :param url: 请求URL
        :param headers: 请求头
        :param params: 查询参数
        :param data: 表单数据
        :param json_data: JSON数据
        :param name: 附件名称
        """
        request_info = {
            "method": method.upper(),
            "url": url,
            "headers": headers or {},
            "params": params or {},
            "data": data or {},
            "json_data": json_data or {}
        }
        
        # 隐藏敏感信息
        sensitive_keys = ['authorization', 'cookie', 'token', 'password']
        for key in sensitive_keys:
            if key in request_info['headers']:
                request_info['headers'][key] = '***HIDDEN***'
        
        AllureUtils.attach_json(request_info, name)
    
    @staticmethod
    def attach_response_details(response: requests.Response, name: str = "Response Details"):
        """
        附加响应详细信息到Allure报告
        :param response: requests响应对象
        :param name: 附件名称
        """
        try:
            # 尝试解析JSON响应
            response_json = response.json()
            response_content = json.dumps(response_json, ensure_ascii=False, indent=2)
            content_type = AttachmentType.JSON
        except (ValueError, json.JSONDecodeError):
            # 如果不是JSON，作为文本处理
            response_content = response.text
            content_type = AttachmentType.TEXT
        
        response_info = {
            "status_code": response.status_code,
            "response_time": f"{response.elapsed.total_seconds():.3f}s",
            "headers": dict(response.headers),
            "content_length": len(response.content),
            "encoding": response.encoding
        }
        
        # 附加响应信息
        AllureUtils.attach_json(response_info, f"{name} - Info")
        
        # 附加响应内容
        allure.attach(
            response_content,
            name=f"{name} - Content",
            attachment_type=content_type
        )
    
    @staticmethod
    def attach_test_data(test_data: Dict[str, Any], name: str = "Test Data"):
        """
        附加测试数据到Allure报告
        :param test_data: 测试数据
        :param name: 附件名称
        """
        AllureUtils.attach_json(test_data, name)
    
    @staticmethod
    def attach_screenshot(image_path: str, name: str = "Screenshot"):
        """
        附加截图到Allure报告
        :param image_path: 图片路径
        :param name: 附件名称
        """
        try:
            with open(image_path, 'rb') as f:
                allure.attach(
                    f.read(),
                    name=name,
                    attachment_type=AttachmentType.PNG
                )
        except Exception as e:
            error(f"附加截图失败: {e}")
    
    @staticmethod
    def attach_file(file_path: str, name: str = None, attachment_type: AttachmentType = AttachmentType.TEXT):
        """
        附加文件到Allure报告
        :param file_path: 文件路径
        :param name: 附件名称
        :param attachment_type: 附件类型
        """
        try:
            with open(file_path, 'rb') as f:
                allure.attach(
                    f.read(),
                    name=name or file_path.split('/')[-1],
                    attachment_type=attachment_type
                )
        except Exception as e:
            error(f"附加文件失败: {e}")
    
    @staticmethod
    def attach_exception(exception: Exception, name: str = "Exception Details"):
        """
        附加异常信息到Allure报告
        :param exception: 异常对象
        :param name: 附件名称
        """
        exception_info = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "traceback": traceback.format_exc()
        }
        
        AllureUtils.attach_json(exception_info, name)
    




# 便捷函数
def attach_response_details(response: requests.Response):
    """将响应详细信息附加到Allure报告"""
    AllureUtils.attach_response_details(response)

def step(step_title: str):
    """Allure步骤装饰器"""
    return AllureUtils.step(step_title)

def attach_text(content: str, name: str = "Text Attachment"):
    """附加文本内容到Allure报告"""
    AllureUtils.attach_text(content, name)

def attach_json(data: Dict[str, Any], name: str = "JSON Data"):
    """附加JSON数据到Allure报告"""
    AllureUtils.attach_json(data, name)

def attach_request_details(method: str, url: str, headers: Dict = None, 
                         params: Dict = None, data: Dict = None, 
                         json_data: Dict = None, name: str = "Request Details"):
    """附加请求详细信息到Allure报告"""
    AllureUtils.attach_request_details(method, url, headers, params, data, json_data, name)

def attach_test_data(test_data: Dict[str, Any], name: str = "Test Data"):
    """附加测试数据到Allure报告"""
    AllureUtils.attach_test_data(test_data, name)

def attach_exception(exception: Exception, name: str = "Exception Details"):
    """附加异常信息到Allure报告"""
    AllureUtils.attach_exception(exception, name)

def allure_test_case(title: str, description: str = ""):
    """测试用例装饰器 - 使用pytest兼容的方式"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with allure.step(f"测试用例: {title}"):
                if description:
                    allure.description(description)
                
                # 记录开始时间
                start_time = time.time()
                
                try:
                    # 执行测试函数
                    result = func(*args, **kwargs)
                    
                    # 记录执行时间
                    execution_time = time.time() - start_time
                    allure.attach(
                        f"执行时间: {execution_time:.2f}秒",
                        "执行时间",
                        allure.attachment_type.TEXT
                    )
                    
                    return result
                except Exception as e:
                    # 记录异常
                    AllureUtils.attach_exception(e, f"测试用例异常: {title}")
                    raise
        return wrapper
    return decorator

# 装饰器已移动到 utils.allure_decorators 模块
# 请使用: from utils.allure_decorators import test_case, api_test, data_driven_test

# 装饰器已移动到 utils.allure_decorators 模块
# 请使用: from utils.allure_decorators import test_case, api_test, data_driven_test

# HTTP请求增强函数
def http_request_with_allure(method: str, url: str, **kwargs):
    """
    带Allure报告的HTTP请求
    :param method: HTTP方法
    :param url: 请求URL
    :param kwargs: 请求参数
    :return: 响应对象
    """
    from utils.http_utils import HTTPUtils
    
    http_utils = HTTPUtils()
    
    with allure.step(f"HTTP请求: {method.upper()} {url}"):
        # 处理json_data参数，转换为json参数
        if 'json_data' in kwargs:
            kwargs['json'] = kwargs.pop('json_data')
        
        # 附加请求详情
        attach_request_details(
            method=method,
            url=url,
            headers=kwargs.get('headers'),
            params=kwargs.get('params'),
            data=kwargs.get('data'),
            json_data=kwargs.get('json')
        )
        
        try:
            # 发送请求
            response = http_utils.request(method, url, **kwargs)
            
            # 附加响应详情
            attach_response_details(response)
            
            return response
        except Exception as e:
            attach_exception(e, f"HTTP请求异常: {method.upper()} {url}")
            raise

# 使用示例
if __name__ == "__main__":
    print("Allure增强工具已创建")
    print("支持的功能:")
    print("- 步骤装饰器: @step('步骤名称')")
    print("- 测试用例装饰器: @test_case('测试标题', '测试描述')")
    print("- API测试装饰器: @api_test('API名称', 'GET', '/api/endpoint')")
    print("- 数据驱动装饰器: @data_driven_test('数据源', 'file')")
    print("- 附件功能: attach_text, attach_json, attach_request_details, attach_response_details") 