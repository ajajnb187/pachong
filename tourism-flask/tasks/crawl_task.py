"""
爬取任务
"""
from datetime import datetime
from celery_worker import celery_app
from crawlers.ctrip_real_crawler import CtripRealCrawler
from utils.hdfs_client import hdfs_client
from utils.data_cleaner import DataCleaner
from utils.logger import logger
from models.database import SessionLocal
from models.task import CrawlerTask

@celery_app.task(bind=True, name='tasks.execute_crawl_task')
def execute_crawl_task(self, task_id, scenic_spot_name, data_source, target_count, data_type):
    """
    执行爬取任务
    
    Args:
        self: Celery任务实例
        task_id: 任务ID
        scenic_spot_name: 景区名称
        data_source: 数据来源 (ctrip/qunar/mafengwo)
        target_count: 目标爬取数量
        data_type: 数据类型 (review/info)
    """
    db = SessionLocal()
    
    try:
        logger.info(f"开始执行爬取任务 {task_id}: {scenic_spot_name}, 来源: {data_source}, 数量: {target_count}")
        
        # 更新任务状态为运行中
        task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        task.status = 'running'
        task.start_time = datetime.now()
        task.progress = 0
        db.commit()
        
        # 选择爬虫（目前只实现了携程）
        if data_source != 'ctrip':
            raise ValueError(f"目前仅支持携程数据源，当前请求: {data_source}")
        
        crawler = CtripRealCrawler()
        
        # 搜索景区ID
        spot_id = crawler.search_scenic_spot(scenic_spot_name)
        if not spot_id:
            raise Exception(f"未找到景区: {scenic_spot_name}")
        
        logger.info(f"景区ID: {spot_id}")
        
        # 爬取数据
        data_list = []
        
        if data_type == 'review':
            # 爬取评价数据
            logger.info(f"开始爬取评价数据...")
            for i, raw_data in enumerate(crawler.crawl_reviews(spot_id, scenic_spot_name, target_count)):
                # 清洗数据
                cleaned_data = DataCleaner.clean_review_data(raw_data)
                if cleaned_data:
                    data_list.append(cleaned_data)
                
                # 更新进度
                progress = min(int((i + 1) / target_count * 100), 100)
                task.progress = progress
                task.actual_count = len(data_list)
                db.commit()
                
                # 每10条输出一次日志
                if (i + 1) % 10 == 0:
                    logger.info(f"任务{task_id}进度: {progress}% ({len(data_list)}/{target_count})")
                
                # 更新Celery任务状态
                self.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'count': len(data_list)}
                )
        
        elif data_type == 'info':
            # 爬取景区信息
            logger.info(f"开始爬取景区信息...")
            info_data = crawler.crawl_info(spot_id, scenic_spot_name)
            if info_data:
                cleaned_data = DataCleaner.clean_scenic_info_data(info_data)
                if cleaned_data:
                    data_list.append(cleaned_data)
            
            task.actual_count = len(data_list)
            task.progress = 100
            db.commit()
        
        else:
            raise Exception(f"不支持的数据类型: {data_type}")
        
        # 检查是否有数据
        if not data_list:
            raise Exception("未爬取到任何数据")
        
        logger.info(f"数据爬取完成，共{len(data_list)}条，开始保存到HDFS...")
        
        # 保存到HDFS
        hdfs_path = hdfs_client.save_data(data_list, task_id, scenic_spot_name, data_source)
        
        if not hdfs_path:
            raise Exception("保存数据到HDFS失败")
        
        # 更新任务状态为成功
        task.status = 'success'
        task.progress = 100
        task.actual_count = len(data_list)
        task.end_time = datetime.now()
        task.hdfs_path = hdfs_path
        db.commit()
        
        logger.info(f"任务{task_id}执行成功，数据已保存到: {hdfs_path}")
        
        return {
            'status': 'success',
            'count': len(data_list),
            'hdfs_path': hdfs_path
        }
        
    except Exception as e:
        # 更新任务状态为失败
        logger.error(f"任务{task_id}执行失败: {str(e)}")
        
        task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if task:
            task.status = 'failed'
            task.error_msg = str(e)
            task.end_time = datetime.now()
            db.commit()
        
        raise
    
    finally:
        db.close()
