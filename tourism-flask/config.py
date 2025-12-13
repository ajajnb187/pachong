"""
Flask爬虫服务配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-for-tourism-flask-2024')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    
    # MySQL数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 23306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root123456')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'tourism_db')
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Celery配置
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://:redis123456@localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://:redis123456@localhost:6379/1')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Shanghai'
    CELERY_ENABLE_UTC = True
    
    # HDFS配置 (Hadoop 3.2.1 使用9870端口)
    HDFS_URL = os.getenv('HDFS_URL', 'http://localhost:9870')
    HDFS_USER = os.getenv('HDFS_USER', 'root')
    
    # 爬虫配置
    CRAWLER_REQUEST_DELAY_MIN = float(os.getenv('CRAWLER_REQUEST_DELAY_MIN', 1.0))  # 最小延迟(秒)
    CRAWLER_REQUEST_DELAY_MAX = float(os.getenv('CRAWLER_REQUEST_DELAY_MAX', 3.0))  # 最大延迟(秒)
    CRAWLER_MAX_RETRIES = int(os.getenv('CRAWLER_MAX_RETRIES', 3))  # 最大重试次数
    CRAWLER_TIMEOUT = int(os.getenv('CRAWLER_TIMEOUT', 30))  # 请求超时时间(秒)
    CRAWLER_THREAD_POOL_SIZE = int(os.getenv('CRAWLER_THREAD_POOL_SIZE', 3))  # 线程池大小
    
    # 代理配置（可选）
    USE_PROXY = os.getenv('USE_PROXY', 'False') == 'True'
    PROXY_SERVER = os.getenv('PROXY_SERVER', '')  # 格式: http://host:port
    PROXY_USERNAME = os.getenv('PROXY_USERNAME', '')
    PROXY_PASSWORD = os.getenv('PROXY_PASSWORD', '')
    PROXY_CHANGE_INTERVAL = int(os.getenv('PROXY_CHANGE_INTERVAL', 5))  # 每N次请求更换代理
    
    # User-Agent池
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    # 福州城市ID（来自参考代码cities.csv）
    FUZHOU_CITY_ID = 164
    
    # 数据存储路径
    DATA_RAW_PATH = os.path.join(os.path.dirname(__file__), 'data', 'raw')
