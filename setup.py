#!/usr/bin/env python3
# coding: utf-8
"""
PythonProject 安装脚本
支持Python 3.8.10环境
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

# 读取requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="pythonproject",
    version="1.0.0",
    description="Python接口自动化测试平台",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="bgtech",
    author_email="bgtech@example.com",
    url="https://github.com/bgtech/pythonproject",
    packages=find_packages(),
    python_requires=">=3.8,<3.9",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: Acceptance",
        "Topic :: Software Development :: Testing :: BDD",
    ],
    keywords=["testing", "api", "automation", "pytest"],
    entry_points={
        "console_scripts": [
            "pythonproject=run:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 