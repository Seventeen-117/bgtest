#!/usr/bin/env python3
# coding: utf-8
"""
快速安装脚本 - 专为Python 3.8.10环境设计
"""

import sys
import subprocess
import os

def main():
    """快速安装主函数"""
    print("🚀 PythonProject 快速安装 (Python 3.8.10)")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8) or sys.version_info >= (3, 9):
        print("❌ 错误: 此项目需要Python 3.8.x版本")
        print(f"当前Python版本: {sys.version}")
        print("请安装Python 3.8.10并重新运行")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 安装依赖
    print("\n📦 安装项目依赖...")
    try:
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements.txt",
            "-i", "https://pypi.tuna.tsinghua.edu.cn/simple/",
            "--upgrade"
        ]
        subprocess.run(cmd, check=True)
        print("✅ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        sys.exit(1)
    
    print("\n🎉 安装完成!")
    print("运行测试: python run.py")

if __name__ == "__main__":
    main() 