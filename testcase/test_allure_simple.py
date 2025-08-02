import pytest
import allure
from utils.allure_utils import (
    step, attach_text, attach_json, attach_test_data, 
    attach_exception
)


class TestAllureSimple:
    """简单Allure功能测试 - 无装饰器"""
    
    def test_basic_allure_features(self):
        """测试Allure的基本功能"""
        with step("准备测试数据"):
            test_data = {
                "name": "测试用户",
                "age": 25,
                "email": "test@example.com"
            }
            attach_test_data(test_data, "测试数据")
        
        with step("执行测试逻辑"):
            # 模拟一些测试逻辑
            result = {"status": "success", "message": "测试通过"}
            attach_json(result, "测试结果")
        
        with step("验证结果"):
            assert result["status"] == "success"
            attach_text("测试验证通过", "验证结果")
    
    def test_mock_api(self):
        """模拟API测试"""
        with step("准备API测试数据"):
            api_data = {
                "endpoint": "/api/test",
                "method": "GET",
                "expected_status": 200
            }
            attach_json(api_data, "API测试数据")
        
        with step("模拟API调用"):
            # 模拟API响应
            mock_response = {
                "status_code": 200,
                "data": {"message": "API调用成功"},
                "headers": {"Content-Type": "application/json"}
            }
            attach_json(mock_response, "模拟API响应")
        
        with step("验证API响应"):
            assert mock_response["status_code"] == 200
            attach_text("API测试验证通过", "API验证结果")
    
    def test_exception_handling(self):
        """测试异常处理功能"""
        with step("准备异常测试"):
            test_data = {"operation": "division", "a": 10, "b": 0}
            attach_test_data(test_data, "异常测试数据")
        
        with step("执行可能异常的操作"):
            try:
                result = test_data["a"] / test_data["b"]
                attach_text(f"计算结果: {result}", "计算结果")
            except ZeroDivisionError as e:
                attach_exception(e, "除零异常")
                # 验证异常被正确捕获
                assert isinstance(e, ZeroDivisionError)
                attach_text("异常被正确捕获和处理", "异常处理结果")
    
    def test_text_attachments(self):
        """测试文本附件功能"""
        with step("创建文本内容"):
            long_text = """
            这是一个很长的文本内容，用于测试Allure的文本附件功能。
            文本可以包含多行内容，并且应该能够正确显示在Allure报告中。
            
            测试要点：
            1. 多行文本显示
            2. 中文字符支持
            3. 特殊字符处理
            4. 格式化显示
            """
            attach_text(long_text, "长文本内容")
        
        with step("创建JSON数据"):
            json_data = {
                "users": [
                    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
                    {"id": 2, "name": "李四", "email": "lisi@example.com"},
                    {"id": 3, "name": "王五", "email": "wangwu@example.com"}
                ],
                "total": 3,
                "page": 1,
                "page_size": 10
            }
            attach_json(json_data, "用户列表数据")
        
        with step("验证数据完整性"):
            assert len(json_data["users"]) == 3
            assert json_data["total"] == 3
            attach_text("数据完整性验证通过", "验证结果")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 