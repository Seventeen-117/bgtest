#!/usr/bin/env python3
# coding: utf-8
"""
项目依赖安装脚本
支持Python 3.8.10环境
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """检查Python版本是否为3.8.x"""
    if sys.version_info < (3, 8) or sys.version_info >= (3, 9):
        print("❌ 错误: 此项目需要Python 3.8.x版本")
        print(f"当前Python版本: {sys.version}")
        print("请安装Python 3.8.10并重新运行此脚本")
        return False
    
    print(f"✅ Python版本检查通过: {sys.version}")
    return True

def check_pip():
    """检查pip是否可用"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print("✅ pip检查通过")
        return True
    except subprocess.CalledProcessError:
        print("❌ pip不可用，请先安装pip")
        return False

def install_requirements():
    """安装项目依赖"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
    
    print("📦 开始安装项目依赖...")
    
    try:
        # 使用国内镜像源安装
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "-r", str(requirements_file),
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/",
            "--upgrade"
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 依赖安装成功")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ 依赖安装失败")
        print(f"错误信息: {e.stderr}")
        return False

def install_dev_dependencies():
    """安装开发依赖"""
    dev_deps = [
        "pytest-cov",
        "black",
        "flake8",
        "mypy"
    ]
    
    print("🔧 安装开发依赖...")
    
    try:
        for dep in dev_deps:
            cmd = [
                sys.executable, "-m", "pip", "install", dep,
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/"
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ 已安装: {dep}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 开发依赖安装失败: {e}")
        return False

def create_virtual_env():
    """创建虚拟环境"""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("ℹ️  虚拟环境已存在")
        return True
    
    print("🔧 创建虚拟环境...")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print("✅ 虚拟环境创建成功")
        print("激活虚拟环境:")
        if os.name == 'nt':  # Windows
            print("  venv\\Scripts\\activate")
        else:  # Linux/macOS
            print("  source venv/bin/activate")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 PythonProject 依赖安装脚本")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查pip
    if not check_pip():
        sys.exit(1)
    
    # 询问是否创建虚拟环境
    create_venv = input("是否创建虚拟环境? (y/n): ").lower().strip()
    if create_venv in ['y', 'yes', '是']:
        if not create_virtual_env():
            sys.exit(1)
    
    # 安装项目依赖
    if not install_requirements():
        sys.exit(1)
    
    # 询问是否安装开发依赖
    install_dev = input("是否安装开发依赖? (y/n): ").lower().strip()
    if install_dev in ['y', 'yes', '是']:
        if not install_dev_dependencies():
            print("⚠️  开发依赖安装失败，但不影响项目运行")
    
    print("\n🎉 安装完成!")
    print("现在可以运行以下命令开始测试:")
    print("  python run.py")

if __name__ == "__main__":
    main() 