import requests
from typing import Dict, Any, Optional, Union
import json
import logging
import time
from common.log import api_info, api_error

# 配置日志
logger = logging.getLogger(__name__)

class HTTPUtils:
    """
    HTTP请求工具类
    支持所有HTTP请求方法：GET、POST、DELETE、PUT、PATCH、HEAD、OPTIONS
    """
    
    def __init__(self, base_url: str = "", default_headers: Optional[Dict] = None, timeout: int = 30):
        """
        初始化HTTP工具类
        :param base_url: 基础URL
        :param default_headers: 默认请求头
        :param timeout: 默认超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.default_timeout = timeout
        self.session = requests.Session()
    
    def _prepare_headers(self, headers: Optional[Dict] = None, token: Optional[str] = None) -> Dict:
        """
        准备请求头
        :param headers: 自定义请求头
        :param token: 认证token
        :return: 合并后的请求头
        """
        final_headers = self.default_headers.copy()
        if headers:
            final_headers.update(headers)
        if token:
            final_headers['Authorization'] = f'Bearer {token}'
        return final_headers
    
    def _log_api_request(self, method: str, url: str, params: Dict = None, 
                        json_data: Dict = None, headers: Dict = None, 
                        start_time: float = None):
        """
        记录API请求信息
        """
        request_info = {
            "timestamp": start_time or time.time(),
            "method": method.upper(),
            "url": url,
            "params": params or {},
            "json_data": json_data or {},
            "headers": {k: v for k, v in (headers or {}).items() if k.lower() not in ['authorization', 'cookie']}
        }
        api_info(f"HTTP请求开始: {json.dumps(request_info, ensure_ascii=False)}")
    
    def _log_api_response(self, method: str, url: str, response: requests.Response, 
                         start_time: float, success: bool = True, error: str = None):
        """
        记录API响应信息
        """
        execution_time = (time.time() - start_time) * 1000
        
        # 安全处理response.content，避免NoneType错误
        response_size = len(response.content) if response.content is not None else 0
        response_info = {
            "timestamp": time.time(),
            "method": method.upper(),
            "url": url,
            "status_code": response.status_code,
            "execution_time_ms": round(execution_time, 2),
            "response_size": response_size,
            "status": "success" if success else "error"
        }
        
        if error:
            response_info["error"] = error
            api_error(f"HTTP请求失败: {json.dumps(response_info, ensure_ascii=False)}")
        else:
            api_info(f"HTTP请求成功: {json.dumps(response_info, ensure_ascii=False)}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求
        :param method: HTTP方法
        :param url: 请求URL
        :param kwargs: 其他请求参数
        :return: 响应对象
        """
        # 构建完整URL
        if not url.startswith(('http://', 'https://')):
            url = f"{self.base_url}/{url.lstrip('/')}"
        
        # 处理json_data参数，转换为json参数
        if 'json_data' in kwargs:
            kwargs['json'] = kwargs.pop('json_data')
        
        # 准备请求头
        headers = self._prepare_headers(
            kwargs.pop('headers', None),
            kwargs.pop('token', None)
        )
        
        # 设置超时时间
        timeout = kwargs.pop('timeout', self.default_timeout)
        
        # 记录请求开始
        start_time = time.time()
        self._log_api_request(
            method=method,
            url=url,
            params=kwargs.get('params'),
            json_data=kwargs.get('json'),
            headers=headers,
            start_time=start_time
        )
        
        # 记录请求信息
        logger.info(f"发送 {method.upper()} 请求到: {url}")
        logger.debug(f"请求头: {headers}")
        if 'json' in kwargs:
            logger.debug(f"请求体(JSON): {kwargs['json']}")
        elif 'data' in kwargs:
            logger.debug(f"请求体(DATA): {kwargs['data']}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
                **kwargs
            )
            
            # 记录响应信息
            logger.info(f"响应状态码: {response.status_code}")
            logger.debug(f"响应头: {dict(response.headers)}")
            
            # 记录API响应
            self._log_api_response(method, url, response, start_time)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            
            # 记录API错误
            self._log_api_response(method, url, requests.Response(), start_time, success=False, error=str(e))
            
            raise
    
    def get(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, 
            token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
        """
        GET请求
        :param url: 请求URL
        :param params: 查询参数
        :param headers: 请求头
        :param token: 认证token
        :param kwargs: 其他参数
        :return: 响应数据
        """
        response = self._make_request('GET', url, params=params, headers=headers, token=token, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None
    
    def post(self, url: str, data: Optional[Union[Dict, str]] = None, json_data: Optional[Dict] = None,
             headers: Optional[Dict] = None, token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
        """
        POST请求
        :param url: 请求URL
        :param data: 表单数据
        :param json_data: JSON数据
        :param headers: 请求头
        :param token: 认证token
        :param kwargs: 其他参数
        :return: 响应数据
        """
        request_kwargs = {}
        if data is not None:
            request_kwargs['data'] = data
        if json_data is not None:
            request_kwargs['json'] = json_data
        
        response = self._make_request('POST', url, headers=headers, token=token, **request_kwargs, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None
    
    def put(self, url: str, data: Optional[Union[Dict, str]] = None, json_data: Optional[Dict] = None,
            headers: Optional[Dict] = None, token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
        """
        PUT请求
        :param url: 请求URL
        :param data: 表单数据
        :param json_data: JSON数据
        :param headers: 请求头
        :param token: 认证token
        :param kwargs: 其他参数
        :return: 响应数据
        """
        request_kwargs = {}
        if data is not None:
            request_kwargs['data'] = data
        if json_data is not None:
            request_kwargs['json'] = json_data
        
        response = self._make_request('PUT', url, headers=headers, token=token, **request_kwargs, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None
    
    def delete(self, url: str, headers: Optional[Dict] = None, token: Optional[str] = None, 
               **kwargs) -> Union[Dict, Any]:
        """
        DELETE请求
        :param url: 请求URL
        :param headers: 请求头
        :param token: 认证token
        :param kwargs: 其他参数
        :return: 响应数据
        """
        response = self._make_request('DELETE', url, headers=headers, token=token, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None
    
    def patch(self, url: str, data: Optional[Union[Dict, str]] = None, json_data: Optional[Dict] = None,
              headers: Optional[Dict] = None, token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
        """
        PATCH请求
        :param url: 请求URL
        :param data: 表单数据
        :param json_data: JSON数据
        :param headers: 请求头
        :param token: 认证token
        :param kwargs: 其他参数
        :return: 响应数据
        """
        request_kwargs = {}
        if data is not None:
            request_kwargs['data'] = data
        if json_data is not None:
            request_kwargs['json'] = json_data
        
        response = self._make_request('PATCH', url, headers=headers, token=token, **request_kwargs, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None
    
    def head(self, url: str, headers: Optional[Dict] = None, token: Optional[str] = None, 
             **kwargs) -> requests.Response:
        """
        HEAD请求
        :param url: 请求URL
        :param headers: 请求头
        :param token: 认证token
        :param kwargs: 其他参数
        :return: 响应对象（HEAD请求通常不返回响应体）
        """
        response = self._make_request('HEAD', url, headers=headers, token=token, **kwargs)
        response.raise_for_status()
        return response
    
    def options(self, url: str, headers: Optional[Dict] = None, token: Optional[str] = None, 
                **kwargs) -> requests.Response:
        """
        OPTIONS请求
        :param url: 请求URL
        :param headers: 请求头
        :param token: 认证token
        :param kwargs: 其他参数
        :return: 响应对象
        """
        response = self._make_request('OPTIONS', url, headers=headers, token=token, **kwargs)
        response.raise_for_status()
        return response
    
    def request(self, method: str, url: str, **kwargs) -> Union[Dict, Any, requests.Response]:
        """
        通用请求方法
        :param method: HTTP方法
        :param url: 请求URL
        :param kwargs: 其他参数
        :return: 响应数据或响应对象
        """
        method = method.upper()
        response = self._make_request(method, url, **kwargs)
        response.raise_for_status()
        
        # HEAD和OPTIONS请求返回响应对象
        if method in ['HEAD', 'OPTIONS']:
            return response
        else:
            return response.json() if response.content else None
    
    def set_default_headers(self, headers: Dict):
        """
        设置默认请求头
        :param headers: 默认请求头
        """
        self.default_headers.update(headers)
    
    def set_token(self, token: str):
        """
        设置默认认证token
        :param token: 认证token
        """
        self.default_headers['Authorization'] = f'Bearer {token}'
    
    def clear_session(self):
        """
        清除会话
        """
        self.session.close()
        self.session = requests.Session()

# 便捷函数（保持向后兼容）
def http_get(url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, 
             token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
    """
    GET请求便捷函数
    """
    http_utils = HTTPUtils()
    try:
        return http_utils.get(url, params=params, headers=headers, token=token, **kwargs)
    finally:
        http_utils.clear_session()

def http_post(url: str, data: Optional[Union[Dict, str]] = None, json_data: Optional[Dict] = None,
              headers: Optional[Dict] = None, token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
    """
    POST请求便捷函数
    """
    http_utils = HTTPUtils()
    try:
        return http_utils.post(url, data=data, json_data=json_data, headers=headers, token=token, **kwargs)
    finally:
        http_utils.clear_session()

def http_put(url: str, data: Optional[Union[Dict, str]] = None, json_data: Optional[Dict] = None,
             headers: Optional[Dict] = None, token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
    """
    PUT请求便捷函数
    """
    http_utils = HTTPUtils()
    try:
        return http_utils.put(url, data=data, json_data=json_data, headers=headers, token=token, **kwargs)
    finally:
        http_utils.clear_session()

def http_delete(url: str, headers: Optional[Dict] = None, token: Optional[str] = None, 
                **kwargs) -> Union[Dict, Any]:
    """
    DELETE请求便捷函数
    """
    http_utils = HTTPUtils()
    try:
        return http_utils.delete(url, headers=headers, token=token, **kwargs)
    finally:
        http_utils.clear_session()

def http_patch(url: str, data: Optional[Union[Dict, str]] = None, json_data: Optional[Dict] = None,
               headers: Optional[Dict] = None, token: Optional[str] = None, **kwargs) -> Union[Dict, Any]:
    """
    PATCH请求便捷函数
    """
    http_utils = HTTPUtils()
    try:
        return http_utils.patch(url, data=data, json_data=json_data, headers=headers, token=token, **kwargs)
    finally:
        http_utils.clear_session()

def http_head(url: str, headers: Optional[Dict] = None, token: Optional[str] = None, 
              **kwargs) -> requests.Response:
    """
    HEAD请求便捷函数
    """
    http_utils = HTTPUtils()
    try:
        return http_utils.head(url, headers=headers, token=token, **kwargs)
    finally:
        http_utils.clear_session()

def http_options(url: str, headers: Optional[Dict] = None, token: Optional[str] = None, 
                **kwargs) -> requests.Response:
    """
    OPTIONS请求便捷函数
    """
    http_utils = HTTPUtils()
    try:
        return http_utils.options(url, headers=headers, token=token, **kwargs)
    finally:
        http_utils.clear_session()

# 使用示例
if __name__ == "__main__":
    # 创建HTTP工具实例
    http_utils = HTTPUtils(base_url="https://api.example.com")
    
    # 设置默认请求头
    http_utils.set_default_headers({
        'Content-Type': 'application/json',
        'User-Agent': 'PythonProject/1.0'
    })
    
    # 设置认证token
    http_utils.set_token("your_token_here")
    
    try:
        # GET请求
        response = http_utils.get("/users", params={"page": 1, "limit": 10})
        print(f"GET响应: {response}")
        
        # POST请求
        user_data = {"name": "John", "email": "john@example.com"}
        response = http_utils.post("/users", json_data=user_data)
        print(f"POST响应: {response}")
        
        # PUT请求
        update_data = {"name": "John Updated"}
        response = http_utils.put("/users/1", json_data=update_data)
        print(f"PUT响应: {response}")
        
        # DELETE请求
        response = http_utils.delete("/users/1")
        print(f"DELETE响应: {response}")
        
        # PATCH请求
        patch_data = {"status": "active"}
        response = http_utils.patch("/users/1", json_data=patch_data)
        print(f"PATCH响应: {response}")
        
        # HEAD请求
        response = http_utils.head("/users")
        print(f"HEAD响应状态码: {response.status_code}")
        print(f"HEAD响应头: {dict(response.headers)}")
        
        # OPTIONS请求
        response = http_utils.options("/users")
        print(f"OPTIONS响应状态码: {response.status_code}")
        print(f"OPTIONS响应头: {dict(response.headers)}")
        
    except Exception as e:
        print(f"请求失败: {e}")
    finally:
        # 清理会话
        http_utils.clear_session()