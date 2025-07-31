import pytest
import os

# 测试执行器

def run_all_tests():
    """
    执行testcase目录下所有用例，并生成HTML报告到report目录
    """
    report_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'report')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    report_file = os.path.join(report_dir, 'report.html')
    pytest.main(['testcase', f'--html={report_file}', '--self-contained-html'])

# 示例用法：
# if __name__ == '__main__':
#     run_all_tests() 