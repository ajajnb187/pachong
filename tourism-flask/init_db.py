"""
初始化Flask应用数据库表
运行此脚本创建crawler_task表
"""
from models.database import init_db
from utils.logger import logger

if __name__ == '__main__':
    logger.info("开始初始化数据库...")
    init_db()
    logger.info("数据库初始化完成！")
    logger.info("crawler_task表已创建")
