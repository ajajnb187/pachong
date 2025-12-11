"""
Celery Worker配置
"""
from celery import Celery
from config import Config

# 创建Celery应用
celery_app = Celery(
    'tourism_crawler',
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
    include=['tasks.crawl_task']
)

# 配置Celery
celery_app.conf.update(
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    accept_content=Config.CELERY_ACCEPT_CONTENT,
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    timezone=Config.CELERY_TIMEZONE,
    enable_utc=Config.CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=3600,  # 任务超时时间：1小时
    worker_prefetch_multiplier=1
)

if __name__ == '__main__':
    celery_app.start()
