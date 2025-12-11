"""
日志工具模块
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 创建日志目录
if not os.path.exists('logs'):
    os.makedirs('logs')

# 配置日志格式
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_logger(name='crawler', level=logging.INFO):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        logger: 日志记录器实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 文件处理器 - 按日期分割
    log_file = f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(log_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(log_format)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建默认日志记录器
logger = get_logger('crawler')
