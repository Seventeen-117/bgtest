#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API监控装饰器
自动记录所有API请求和响应到api_monitor.log
"""

import time
import json
import functools
from typing import Dict, Any, Optional
from common.log import api_info, api_error

def api_monitor(func):
    """
    API监控装饰器
    自动记录API请求和响应信息
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 获取函数信息
        func_name = func.__name__
        module_name = func.__module__
        
        # 记录请求开始
        request_info = {
            "timestamp": time.time(),
            "function": f"{module_name}.{func_name}",
            "args": str(args),
            "kwargs": str(kwargs)
        }
        
        api_info(f"API请求开始: {json.dumps(request_info, ensure_ascii=False)}")
        
        start_time = time.time()
        
        try:
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 计算执行时间
            execution_time = (time.time() - start_time) * 1000
            
            # 记录响应信息
            response_info = {
                "timestamp": time.time(),
                "function": f"{module_name}.{func_name}",
                "execution_time_ms": round(execution_time, 2),
                "status": "success",
                "result": str(result)[:500]  # 限制结果长度
            }
            
            api_info(f"API请求成功: {json.dumps(response_info, ensure_ascii=False)}")
            
            return result
            
        except Exception as e:
            # 计算执行时间
            execution_time = (time.time() - start_time) * 1000
            
            # 记录错误信息
            error_info = {
                "timestamp": time.time(),
                "function": f"{module_name}.{func_name}",
                "execution_time_ms": round(execution_time, 2),
                "status": "error",
                "error": str(e)
            }
            
            api_error(f"API请求失败: {json.dumps(error_info, ensure_ascii=False)}")
            
            raise
    
    return wrapper

def http_monitor(url: str = None, method: str = None):
    """
    HTTP请求监控装饰器
    专门用于监控HTTP请求
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取请求信息
            request_url = url or kwargs.get('url') or (args[0] if args else 'unknown')
            request_method = method or kwargs.get('method') or 'unknown'
            
            # 记录请求开始
            request_info = {
                "timestamp": time.time(),
                "url": request_url,
                "method": request_method.upper(),
                "params": kwargs.get('params', {}),
                "json_data": kwargs.get('json_data', {}),
                "headers": kwargs.get('headers', {})
            }
            
            api_info(f"HTTP请求开始: {json.dumps(request_info, ensure_ascii=False)}")
            
            start_time = time.time()
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 计算执行时间
                execution_time = (time.time() - start_time) * 1000
                
                # 记录响应信息
                response_info = {
                    "timestamp": time.time(),
                    "url": request_url,
                    "method": request_method.upper(),
                    "execution_time_ms": round(execution_time, 2),
                    "status_code": getattr(result, 'status_code', None),
                    "status": "success",
                    "response_size": len(str(result)) if result else 0
                }
                
                api_info(f"HTTP请求成功: {json.dumps(response_info, ensure_ascii=False)}")
                
                return result
                
            except Exception as e:
                # 计算执行时间
                execution_time = (time.time() - start_time) * 1000
                
                # 记录错误信息
                error_info = {
                    "timestamp": time.time(),
                    "url": request_url,
                    "method": request_method.upper(),
                    "execution_time_ms": round(execution_time, 2),
                    "status": "error",
                    "error": str(e)
                }
                
                api_error(f"HTTP请求失败: {json.dumps(error_info, ensure_ascii=False)}")
                
                raise
        
        return wrapper
    return decorator

class APIMonitor:
    """API监控类"""
    
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_time = 0
    
    def record_request(self, url: str, method: str, params: Dict = None, 
                      response: Any = None, error: Exception = None, 
                      execution_time: float = 0):
        """
        记录API请求
        :param url: 请求URL
        :param method: 请求方法
        :param params: 请求参数
        :param response: 响应结果
        :param error: 错误信息
        :param execution_time: 执行时间
        """
        self.request_count += 1
        
        if error:
            self.error_count += 1
            status = "error"
        else:
            self.success_count += 1
            status = "success"
        
        self.total_time += execution_time
        
        # 构建监控信息
        monitor_info = {
            "timestamp": time.time(),
            "url": url,
            "method": method.upper(),
            "params": params or {},
            "status": status,
            "execution_time_ms": round(execution_time * 1000, 2),
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_time_ms": round((self.total_time / self.request_count) * 1000, 2) if self.request_count > 0 else 0
        }
        
        if error:
            monitor_info["error"] = str(error)
            api_error(f"API监控记录: {json.dumps(monitor_info, ensure_ascii=False)}")
        else:
            monitor_info["response_size"] = len(str(response)) if response else 0
            api_info(f"API监控记录: {json.dumps(monitor_info, ensure_ascii=False)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取监控统计信息
        :return: 统计信息
        """
        return {
            "total_requests": self.request_count,
            "success_requests": self.success_count,
            "error_requests": self.error_count,
            "success_rate": round(self.success_count / self.request_count * 100, 2) if self.request_count > 0 else 0,
            "avg_execution_time_ms": round((self.total_time / self.request_count) * 1000, 2) if self.request_count > 0 else 0,
            "total_execution_time_ms": round(self.total_time * 1000, 2)
        }

# 全局API监控实例
api_monitor = APIMonitor()

def monitor_api_request(url: str, method: str, params: Dict = None):
    """
    监控API请求的装饰器
    :param url: 请求URL
    :param method: 请求方法
    :param params: 请求参数
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # 执行原函数
                result = func(*args, **kwargs)
                
                # 计算执行时间
                execution_time = time.time() - start_time
                
                # 记录请求
                api_monitor.record_request(
                    url=url,
                    method=method,
                    params=params,
                    response=result,
                    execution_time=execution_time
                )
                
                return result
                
            except Exception as e:
                # 计算执行时间
                execution_time = time.time() - start_time
                
                # 记录错误
                api_monitor.record_request(
                    url=url,
                    method=method,
                    params=params,
                    error=e,
                    execution_time=execution_time
                )
                
                raise
        
        return wrapper
    return decorator

# 使用示例
if __name__ == "__main__":
    # 测试API监控装饰器
    @api_monitor
    def test_function():
        time.sleep(0.1)
        return {"status": "success"}
    
    # 测试HTTP监控装饰器
    @http_monitor(url="https://api.example.com/test", method="GET")
    def test_http_request():
        time.sleep(0.1)
        return {"status": "success"}
    
    # 测试监控API请求装饰器
    @monitor_api_request(url="https://api.example.com/test", method="POST", params={"test": "value"})
    def test_monitored_request():
        time.sleep(0.1)
        return {"status": "success"}
    
    print("测试API监控功能...")
    
    try:
        test_function()
        test_http_request()
        test_monitored_request()
        
        # 获取统计信息
        stats = api_monitor.get_statistics()
        print(f"API监控统计: {stats}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    
    print("API监控测试完成！") 