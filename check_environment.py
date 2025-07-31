#!/usr/bin/env python3
# coding: utf-8
"""
环境检查脚本 - 验证Python 3.8.10环境和项目依赖
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    
    if sys.version_info < (3, 8) or sys.version_info >= (3, 9):
        print(f"❌ Python版本不兼容: {sys.version}")
        print("   需要Python 3.8.x版本")
        return False
    
    print(f"✅ Python版本: {sys.version}")
    return True

def check_pip():
    """检查pip"""
    print("\n🔍 检查pip...")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ pip版本: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip不可用")
        return False

def check_package(package_name, import_name=None):
    """检查包是否已安装"""
    if import_name is None:
        import_name = package_name.replace("-", "_")
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: 未安装")
        return False

def check_requirements():
    """检查requirements.txt中的依赖"""
    print("\n🔍 检查项目依赖...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
    
    # 读取requirements.txt
    with open(requirements_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 解析依赖包
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # 提取包名（去掉版本号）
            package = line.split('>=')[0].split('<')[0].split('==')[0].strip()
            packages.append(package)
    
    # 检查每个包
    success_count = 0
    for package in packages:
        if check_package(package):
            success_count += 1
    
    print(f"\n📊 依赖检查结果: {success_count}/{len(packages)} 个包已安装")
    return success_count == len(packages)

def check_project_structure():
    """检查项目结构"""
    print("\n🔍 检查项目结构...")
    
    required_dirs = [
        "caseparams",
        "common", 
        "conf",
        "data_prepare",
        "design",
        "execution",
        "log",
        "report",
        "testcase",
        "utils"
    ]
    
    required_files = [
        "requirements.txt",
        "pytest.ini",
        "run.py",
        "README.md"
    ]
    
    missing_dirs = []
    missing_files = []
    
    # 检查目录
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ 目录: {dir_name}")
        else:
            print(f"❌ 目录: {dir_name}")
            missing_dirs.append(dir_name)
    
    # 检查文件
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"✅ 文件: {file_name}")
        else:
            print(f"❌ 文件: {file_name}")
            missing_files.append(file_name)
    
    return len(missing_dirs) == 0 and len(missing_files) == 0

def check_pytest():
    """检查pytest配置"""
    print("\n🔍 检查pytest配置...")
    
    pytest_ini = Path("pytest.ini")
    if not pytest_ini.exists():
        print("❌ pytest.ini文件不存在")
        return False
    
    try:
        with open(pytest_ini, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "python_version" in content:
            print("✅ pytest.ini包含Python版本配置")
        else:
            print("⚠️  pytest.ini缺少Python版本配置")
        
        return True
    except Exception as e:
        print(f"❌ 读取pytest.ini失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 PythonProject 环境检查")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("pip", check_pip),
        ("项目依赖", check_requirements),
        ("项目结构", check_project_structure),
        ("pytest配置", check_pytest)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}检查失败: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 检查总结:")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总体结果: {success_count}/{total_count} 项检查通过")
    
    if success_count == total_count:
        print("🎉 环境检查全部通过! 可以开始使用项目")
        print("运行测试: python run.py")
    else:
        print("⚠️  部分检查失败，请解决上述问题后重试")
        print("安装依赖: python install_dependencies.py")

if __name__ == "__main__":
    main() 