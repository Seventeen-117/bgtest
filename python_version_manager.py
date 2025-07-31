#!/usr/bin/env python3
# coding: utf-8
"""
Python版本管理工具
用于卸载现有Python版本并安装Python 3.8.10
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pathlib import Path

def print_step(step_num, description):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {description}")
    print(f"{'='*60}")

def run_command(command, check=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        if check and result.returncode != 0:
            print(f"命令执行失败: {command}")
            print(f"错误信息: {result.stderr}")
            return False
        return result
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False

def check_admin_rights():
    """检查是否有管理员权限"""
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def get_python_installations():
    """获取已安装的Python版本"""
    installations = []
    
    # 检查py启动器
    result = run_command("py -0", check=False)
    if result and result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if 'Python' in line and '64-bit' in line:
                version = line.split()[1]
                installations.append(version)
    
    # 检查常见安装路径
    common_paths = [
        r"C:\Python*",
        r"C:\Users\{}\AppData\Local\Programs\Python\Python*".format(os.getenv('USERNAME')),
        r"C:\Program Files\Python*",
        r"C:\Program Files (x86)\Python*"
    ]
    
    for path_pattern in common_paths:
        for path in Path("C:\\").glob(path_pattern.replace("C:\\", "")):
            if path.is_dir():
                python_exe = path / "python.exe"
                if python_exe.exists():
                    try:
                        result = run_command(f'"{python_exe}" --version', check=False)
                        if result and result.returncode == 0:
                            version = result.stdout.strip().split()[1]
                            installations.append(version)
                    except:
                        pass
    
    return list(set(installations))

def uninstall_python_windows(version):
    """在Windows上卸载Python"""
    print(f"正在卸载Python {version}...")
    
    # 方法1: 使用控制面板卸载
    print("方法1: 尝试通过控制面板卸载...")
    result = run_command(f'wmic product where "name like \'%Python {version}%\'" call uninstall /nointeractive', check=False)
    
    # 方法2: 使用py启动器卸载
    print("方法2: 尝试通过py启动器卸载...")
    result = run_command(f'py -{version} -m pip uninstall pip setuptools wheel -y', check=False)
    
    # 方法3: 手动删除目录
    print("方法3: 手动删除Python目录...")
    common_paths = [
        rf"C:\Python{version.replace('.', '')}",
        rf"C:\Users\{os.getenv('USERNAME')}\AppData\Local\Programs\Python\Python{version}",
        rf"C:\Program Files\Python{version}",
        rf"C:\Program Files (x86)\Python{version}"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"已删除目录: {path}")
            except Exception as e:
                print(f"删除目录失败 {path}: {e}")
    
    print(f"Python {version} 卸载完成")

def download_python_3810():
    """下载Python 3.8.10"""
    print("正在下载Python 3.8.10...")
    
    # Python 3.8.10下载链接
    download_url = "https://www.python.org/ftp/python/3.8.10/python-3.8.10-amd64.exe"
    installer_path = "python-3.8.10-amd64.exe"
    
    try:
        print(f"从 {download_url} 下载...")
        urllib.request.urlretrieve(download_url, installer_path)
        print(f"下载完成: {installer_path}")
        return installer_path
    except Exception as e:
        print(f"下载失败: {e}")
        return None

def install_python_3810(installer_path):
    """安装Python 3.8.10"""
    print("正在安装Python 3.8.10...")
    
    # 安装命令
    install_command = f'"{installer_path}" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0'
    
    print("请以管理员身份运行以下命令:")
    print(f"  {install_command}")
    print("\n或者手动运行安装程序并选择:")
    print("  - Install for all users")
    print("  - Add Python to PATH")
    print("  - Install pip")
    
    # 尝试自动安装
    if check_admin_rights():
        print("检测到管理员权限，尝试自动安装...")
        result = run_command(install_command)
        if result:
            print("Python 3.8.10 安装完成")
            return True
    else:
        print("需要管理员权限进行安装")
        return False

def verify_installation():
    """验证Python 3.8.10安装"""
    print("验证Python 3.8.10安装...")
    
    # 检查py启动器
    result = run_command("py -3.8 --version", check=False)
    if result and result.returncode == 0:
        print(f"Python 3.8.10 安装成功: {result.stdout.strip()}")
        return True
    
    # 检查直接路径
    common_paths = [
        r"C:\Python38\python.exe",
        r"C:\Users\{}\AppData\Local\Programs\Python\Python38\python.exe".format(os.getenv('USERNAME')),
        r"C:\Program Files\Python38\python.exe"
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            result = run_command(f'"{path}" --version', check=False)
            if result and result.returncode == 0:
                print(f"Python 3.8.10 安装成功: {result.stdout.strip()}")
                return True
    
    print("Python 3.8.10 安装验证失败")
    return False

def main():
    """主函数"""
    print("Python版本管理工具")
    print("=" * 60)
    
    # 检查操作系统
    if platform.system() != "Windows":
        print("此脚本仅支持Windows系统")
        return
    
    # 检查管理员权限
    if not check_admin_rights():
        print("警告: 建议以管理员身份运行此脚本")
        print("请右键点击PowerShell/命令提示符，选择'以管理员身份运行'")
        input("按Enter键继续...")
    
    # 步骤1: 检查现有安装
    print_step(1, "检查现有Python安装")
    installations = get_python_installations()
    print(f"发现已安装的Python版本: {installations}")
    
    # 步骤2: 卸载Python 3.13和3.12
    print_step(2, "卸载Python 3.13和3.12")
    for version in ['3.13', '3.12']:
        if version in installations:
            uninstall_python_windows(version)
        else:
            print(f"未发现Python {version}安装")
    
    # 步骤3: 下载Python 3.8.10
    print_step(3, "下载Python 3.8.10")
    installer_path = download_python_3810()
    if not installer_path:
        print("下载失败，请手动下载Python 3.8.10")
        print("下载地址: https://www.python.org/downloads/release/python-3810/")
        return
    
    # 步骤4: 安装Python 3.8.10
    print_step(4, "安装Python 3.8.10")
    if install_python_3810(installer_path):
        # 步骤5: 验证安装
        print_step(5, "验证安装")
        if verify_installation():
            print("\n✅ Python 3.8.10 安装成功!")
            print("\n下一步:")
            print("1. 重新打开命令提示符或PowerShell")
            print("2. 运行: python --version")
            print("3. 运行: py -3.8 --version")
            print("4. 在项目目录中运行: python check_environment.py")
        else:
            print("\n❌ Python 3.8.10 安装验证失败")
            print("请手动检查安装")
    else:
        print("\n❌ Python 3.8.10 安装失败")
        print("请手动运行安装程序")
    
    # 清理下载文件
    if os.path.exists(installer_path):
        try:
            os.remove(installer_path)
            print(f"已清理下载文件: {installer_path}")
        except:
            pass

if __name__ == "__main__":
    main() 