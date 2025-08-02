# coding: utf-8
# @Author: bgtech
import pytest
import allure


@allure.feature("断言工具测试")
class TestAssertionUtils:
    """断言工具测试类"""

    @pytest.mark.unit
    def test_assertion_utils_fixture(self, assertion_utils):
        """测试断言工具fixture"""
        with allure.step("测试断言工具基本功能"):
            # 测试基本断言
            assertion_utils.assert_equal(1, 1, "基本相等断言")
            assertion_utils.assert_true(True, "真值断言")
            assertion_utils.assert_false(False, "假值断言")
            assertion_utils.assert_not_none("test", "非空断言")
            
            # 测试包含断言
            assertion_utils.assert_in("test", ["test", "example"], "包含断言")
            assertion_utils.assert_contains("hello world", "world", "文本包含断言")
            
            # 测试统计功能
            stats = assertion_utils.get_assertion_stats()
            assert stats['total'] >= 6, f"断言总数应该至少为6，实际为{stats['total']}"
            assert stats['passed'] >= 6, f"通过断言数应该至少为6，实际为{stats['passed']}"
            assert stats['failed'] == 0, f"失败断言数应该为0，实际为{stats['failed']}"
            
            allure.attach(
                str(stats),
                name="断言统计",
                attachment_type=allure.attachment_type.TEXT
            )

    @pytest.mark.unit
    def test_assertion_utils_status_code(self, assertion_utils):
        """测试状态码断言"""
        with allure.step("测试状态码断言功能"):
            # 模拟响应对象
            mock_response = {"status_code": 200}
            assertion_utils.assert_status_code(mock_response, 200)
            
            # 测试失败情况
            try:
                assertion_utils.assert_status_code(mock_response, 404)
                assert False, "应该抛出AssertionError"
            except AssertionError:
                # 预期的失败
                pass

    @pytest.mark.unit
    def test_assertion_utils_response_contains(self, assertion_utils):
        """测试响应包含断言"""
        with allure.step("测试响应包含断言功能"):
            # 测试字典响应
            dict_response = {"message": "success", "data": {"id": 123}}
            assertion_utils.assert_response_contains(dict_response, "success")
            
            # 测试字符串响应
            str_response = "Hello World"
            assertion_utils.assert_response_contains(str_response, "World")
            
            # 测试失败情况
            try:
                assertion_utils.assert_response_contains(dict_response, "failure")
                assert False, "应该抛出AssertionError"
            except AssertionError:
                # 预期的失败
                pass

    @pytest.mark.unit
    def test_assertion_utils_regex_match(self, assertion_utils):
        """测试正则表达式断言"""
        with allure.step("测试正则表达式断言功能"):
            text = "Hello World 123"
            assertion_utils.assert_regex_match(r"World \d+", text)
            assertion_utils.assert_regex_match(r"^Hello", text)
            
            # 测试失败情况
            try:
                assertion_utils.assert_regex_match(r"^Failure", text)
                assert False, "应该抛出AssertionError"
            except AssertionError:
                # 预期的失败
                pass

    @pytest.mark.unit
    def test_assertion_utils_json_structure(self, assertion_utils):
        """测试JSON结构断言"""
        with allure.step("测试JSON结构断言功能"):
            response = {
                "status": "success",
                "data": {"id": 123, "name": "test"},
                "message": "OK"
            }
            expected_structure = ["status", "data", "message"]
            assertion_utils.assert_json_structure(response, expected_structure)
            
            # 测试失败情况
            try:
                assertion_utils.assert_json_structure(response, ["status", "missing_field"])
                assert False, "应该抛出AssertionError"
            except AssertionError:
                # 预期的失败
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 