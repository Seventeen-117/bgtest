import pytest
import allure
from utils.allure_utils import (
    step, attach_text, attach_json, attach_test_data, 
    attach_exception
)
from utils.allure_decorators import (
    performance_test, security_test
)
from common.get_caseparams import read_test_data


class TestAllureWithDecorators:
    @performance_test(threshold_ms=500.0)
    def test_performance(self):
        """性能测试"""
        with step("执行性能测试"):
            import time
            # 模拟一些耗时操作
            time.sleep(0.1)  # 100ms
            
            result = {"execution_time": 100, "status": "success"}
            attach_json(result, "性能测试结果")
        
        with step("验证性能结果"):
            assert result["execution_time"] < 500
            attach_text("性能测试通过", "性能验证结果")
    
    @security_test(security_level="high")
    def test_security(self):
        """安全测试"""
        with step("执行安全测试"):
            security_data = {
                "test_type": "authentication",
                "security_level": "high",
                "vulnerabilities_found": 0
            }
            attach_json(security_data, "安全测试数据")
        
        with step("验证安全结果"):
            assert security_data["vulnerabilities_found"] == 0
            attach_text("安全测试通过", "安全验证结果")
    
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.feature("异常处理")
    @allure.story("异常捕获测试")
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
    
    @allure.severity(allure.severity_level.NORMAL)
    @allure.feature("文本处理")
    @allure.story("文本附件测试")
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