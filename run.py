# coding: utf-8
# @Author: bgtech
import pytest
import os
import sys
import argparse
import datetime
from pathlib import Path


def setup_environment():
    """设置测试环境"""
    # 确保必要的目录存在
    directories = ['report', 'log', 'temp']
    for dir_name in directories:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"创建目录: {dir_path}")


def generate_report_filename(report_type="html"):
    """生成报告文件名"""
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("report")
    
    if report_type == "html":
        return report_dir / f"test_report_{now}.html"
    elif report_type == "allure":
        return report_dir / f"allure-results-{now}"
    else:
        return report_dir / f"report_{now}.{report_type}"


def build_pytest_args(args):
    """构建pytest参数"""
    pytest_args = [
        "testcase",  # 执行testcase目录下的所有测试
        '-s',  # 显示print输出
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误回溯
        "--strict-markers",  # 严格标记检查
        "--disable-warnings",  # 禁用警告
    ]
    
    # 根据命令行参数添加选项
    if args.markers:
        pytest_args.extend(["-m", args.markers])
    
    if args.keyword:
        pytest_args.extend(["-k", args.keyword])
    
    if args.maxfail:
        pytest_args.extend(["--maxfail", str(args.maxfail)])
    
    if args.workers:
        pytest_args.extend(["-n", str(args.workers)])
    
    # 默认生成所有报告，除非指定了 --no-reports
    should_generate_reports = not args.no_reports
    
    # 添加HTML报告
    if should_generate_reports or args.html:
        try:
            import pytest_html
            html_file = generate_report_filename("html")
            pytest_args.extend([
                f"--html={html_file}",
                "--self-contained-html"
            ])
            print(f"将生成HTML报告: {html_file}")
        except ImportError:
            print("警告: pytest-html插件未安装，跳过HTML报告生成")
            print("请运行: pip install pytest-html")
    
    # 添加Allure报告
    if should_generate_reports or args.allure:
        try:
            import allure
            allure_dir = generate_report_filename("allure")
            pytest_args.extend([
                f"--alluredir={allure_dir}",
                "--clean-alluredir"
            ])
            print(f"将生成Allure报告: {allure_dir}")
        except ImportError:
            print("警告: allure-pytest插件未安装，跳过Allure报告生成")
            print("请运行: pip install allure-pytest")
    
    # 添加覆盖率报告
    if should_generate_reports or args.coverage:
        try:
            import pytest_cov
            pytest_args.extend([
                "--cov=testcase",
                "--cov-report=html:report/coverage",
                "--cov-report=term-missing"
            ])
            print("将生成覆盖率报告")
        except ImportError:
            print("警告: pytest-cov插件未安装，跳过覆盖率报告生成")
            print("请运行: pip install pytest-cov")
    
    # 添加并行执行
    if args.parallel:
        try:
            import pytest_xdist
            pytest_args.extend(["-n", "auto"])
            print("将使用并行执行")
        except ImportError:
            print("警告: pytest-xdist插件未安装，将使用串行执行")
            print("请运行: pip install pytest-xdist")
    
    return pytest_args


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="统一执行testcase目录下的所有测试用例",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run.py                           # 执行所有测试并生成所有报告
  python run.py --no-reports             # 执行所有测试但不生成报告
  python run.py -m "smoke"               # 执行标记为smoke的测试并生成所有报告
  python run.py -k "login"               # 执行包含login的测试并生成所有报告
  python run.py --html                   # 只生成HTML报告
  python run.py --allure                 # 只生成Allure报告
  python run.py --coverage               # 只生成覆盖率报告
  python run.py --parallel               # 并行执行测试并生成所有报告
  python run.py --maxfail 3              # 最多失败3个测试后停止
        """
    )
    
    # 测试选择参数
    parser.add_argument(
        "-m", "--markers",
        help="只运行指定标记的测试 (例如: smoke, api, unit)"
    )
    parser.add_argument(
        "-k", "--keyword",
        help="只运行包含指定关键字的测试"
    )
    parser.add_argument(
        "--maxfail",
        type=int,
        help="最多失败多少个测试后停止"
    )
    
    # 报告参数
    parser.add_argument(
        "--html",
        action="store_true",
        help="生成HTML报告"
    )
    parser.add_argument(
        "--allure",
        action="store_true",
        help="生成Allure报告"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="生成覆盖率报告"
    )
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="不生成任何报告 (默认会生成所有报告)"
    )
    
    # 执行参数
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="并行执行测试"
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="指定并行工作进程数"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示将要执行的测试，不实际执行"
    )
    
    return parser.parse_args()


def list_available_tests():
    """列出可用的测试"""
    print("可用的测试文件:")
    testcase_dir = Path("testcase")
    if testcase_dir.exists():
        for test_file in testcase_dir.glob("test_*.py"):
            print(f"  - {test_file}")
    else:
        print("  testcase目录不存在")


def main():
    """主函数"""
    print("=" * 60)
    print("测试执行器 - 统一执行testcase目录下的所有测试用例")
    print("=" * 60)
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置环境
    setup_environment()
    
    # 检查testcase目录是否存在
    if not Path("testcase").exists():
        print("错误: testcase目录不存在!")
        sys.exit(1)
    
    # 如果是dry-run模式，只列出测试
    if args.dry_run:
        list_available_tests()
        return
    
    # 构建pytest参数
    pytest_args = build_pytest_args(args)
    
    # 显示执行信息
    print(f"执行目录: testcase")
    print(f"pytest参数: {' '.join(pytest_args)}")
    print("-" * 60)
    
    # 执行pytest
    print("开始执行测试...")
    start_time = datetime.datetime.now()
    
    try:
        exit_code = pytest.main(pytest_args)
    except Exception as e:
        print(f"执行测试时发生错误: {e}")
        exit_code = 1
    
    end_time = datetime.datetime.now()
    duration = end_time - start_time
    
    # 显示执行结果
    print("-" * 60)
    print(f"测试执行完成!")
    print(f"执行时间: {duration}")
    print(f"退出码: {exit_code}")
    
    if exit_code == 0:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败!")
    
    # 如果生成了Allure报告，提示如何查看
    if args.allure:
        try:
            import allure
            allure_dir = generate_report_filename("allure")
            print(f"\n📊 Allure报告已生成: {allure_dir}")
            print("查看报告命令: allure serve " + str(allure_dir))
        except ImportError:
            pass
    
    # 如果生成了覆盖率报告，提示查看位置
    if args.coverage:
        print(f"\n📈 覆盖率报告已生成: report/coverage/index.html")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()