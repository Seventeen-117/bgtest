# coding: utf-8
# @Author: bgtech
import pytest
import os
import sys



if __name__ == "__main__":

    
    # 确保report目录存在
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'report')
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # 生成带时间戳的报告文件名
    import datetime
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(report_dir, f"report_{now}.html")
    
    # 构建pytest参数
    pytest_args = [
        "testcase",
        '-s',
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误回溯
    ]
    
    # 检查是否安装了pytest-html插件
    try:
        import pytest_html
        # 如果插件可用，添加HTML报告参数
        pytest_args.extend([
            f"--html={report_file}",
            "--self-contained-html"
        ])
        print(f"将生成HTML报告: {report_file}")
    except ImportError:
        print("警告: pytest-html插件未安装，将不会生成HTML报告")
        print("请运行: pip install pytest-html")
    
    # 执行pytest
    print("开始执行测试...")
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("测试执行完成!")
    else:
        print(f"测试执行失败，退出码: {exit_code}")
    
    sys.exit(exit_code)