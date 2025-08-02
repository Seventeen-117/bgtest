import pytest
import allure
from utils.allure_utils import (
    step, attach_text, attach_json, attach_test_data,
    attach_exception
)
from utils.allure_decorators import allure_test_case, allure_api_test, allure_data_driven_test
from common.get_caseparams import read_test_data


class TestAllureBasic:
    """基础Allure功能测试 - 无网络依赖"""

    @allure_test_case("基础Allure功能测试", "测试Allure的基本功能")
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

    @allure_api_test("模拟API测试", "GET", "/api/test")
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

    @allure_data_driven_test("caseparams/test_chat_gateway.yaml", "file")
    def test_data_driven_mock(self):
        """数据驱动测试 - 模拟版本"""
        # 读取测试数据
        test_data = read_test_data('caseparams/test_chat_gateway.yaml')

        for case in test_data:
            with step(f"执行测试用例: {case.get('case_id', 'Unknown')}"):
                case_id = case.get('case_id')
                description = case.get('description', 'No description')
                params = case.get('params', {})
                expected = case.get('expected_result', {})

                # 附加测试用例信息
                attach_test_data(case, f"测试用例: {case_id}")

                with step("模拟请求处理"):
                    # 模拟请求处理逻辑
                    mock_response = {
                        "status_code": 200,
                        "data": {"message": f"处理用例 {case_id}"},
                        "params_received": params
                    }
                    attach_json(mock_response, f"用例 {case_id} 响应")

                with step("验证处理结果"):
                    assert mock_response["status_code"] == 200
                    attach_text(f"用例 {case_id} 处理成功", "处理结果")

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