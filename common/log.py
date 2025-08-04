import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 获取log目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(base_dir, 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, 'log.log')
api_monitor_file = os.path.join(log_dir, 'api_monitor.log')

# 创建主logger
logger = logging.getLogger('project_logger')
logger.setLevel(logging.INFO)

# 文件日志处理器（每天轮转，保留7天）
file_handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=7, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
file_handler.setFormatter(file_fmt)

# 控制台日志处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
console_handler.setFormatter(console_fmt)

# API监控日志logger
api_logger = logging.getLogger('api_monitor_logger')
api_logger.setLevel(logging.INFO)
api_file_handler = TimedRotatingFileHandler(api_monitor_file, when='midnight', backupCount=7, encoding='utf-8')
api_file_handler.setLevel(logging.INFO)
api_fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
api_file_handler.setFormatter(api_fmt)
if not api_logger.handlers:
    api_logger.addHandler(api_file_handler)

# 避免重复添加handler
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# 日志输出函数
def info(msg):
    logger.info(msg)

def error(msg):
    logger.error(msg)

def debug(msg):
    logger.debug(msg)

def warn(msg):
    """警告日志输出函数"""
    logger.warning(msg)

# API监控日志输出函数
def api_info(msg):
    """记录接口请求和响应数据"""
    api_logger.info(msg)

def api_error(msg):
    """记录接口异常信息"""
    api_logger.error(msg) 