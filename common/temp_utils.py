import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, 'temp')

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def write_temp_file(filename, content, mode='w', encoding='utf-8'):
    """
    写入临时文件
    :param filename: 文件名（不含路径）
    :param content: 内容（str或bytes）
    :param mode: 写入模式，'w'或'wb'
    :param encoding: 文本编码
    :return: 文件完整路径
    """
    file_path = os.path.join(TEMP_DIR, filename)
    with open(file_path, mode, encoding=encoding if 'b' not in mode else None) as f:
        f.write(content)
    return file_path

def read_temp_file(filename, mode='r', encoding='utf-8'):
    """
    读取临时文件
    :param filename: 文件名（不含路径）
    :param mode: 读取模式，'r'或'rb'
    :param encoding: 文本编码
    :return: 文件内容
    """
    file_path = os.path.join(TEMP_DIR, filename)
    with open(file_path, mode, encoding=encoding if 'b' not in mode else None) as f:
        return f.read()

def clean_temp_dir():
    """
    清空temp目录下所有临时文件
    """
    for fname in os.listdir(TEMP_DIR):
        fpath = os.path.join(TEMP_DIR, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)
        elif os.path.isdir(fpath):
            shutil.rmtree(fpath) 