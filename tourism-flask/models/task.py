"""
爬取任务模型
"""
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from models.database import Base

class CrawlerTask(Base):
    """爬取任务表"""
    
    __tablename__ = 'crawler_task'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='任务ID')
    task_name = Column(String(100), nullable=False, comment='任务名称')
    scenic_spot_name = Column(String(100), nullable=False, comment='景区名称')
    data_source = Column(String(50), nullable=False, comment='数据来源')
    target_count = Column(Integer, default=100, comment='目标爬取数量')
    actual_count = Column(Integer, default=0, comment='实际爬取数量')
    status = Column(String(20), default='pending', comment='任务状态')
    progress = Column(Integer, default=0, comment='进度')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    error_msg = Column(Text, comment='错误信息')
    hdfs_path = Column(String(500), comment='HDFS存储路径')
    create_by = Column(BigInteger, comment='创建人ID')
    create_time = Column(DateTime, default=func.now(), comment='创建时间')
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.id,
            'task_name': self.task_name,
            'scenic_spot_name': self.scenic_spot_name,
            'data_source': self.data_source,
            'target_count': self.target_count,
            'actual_count': self.actual_count,
            'crawled_count': self.actual_count,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'error_msg': self.error_msg,
            'hdfs_path': self.hdfs_path,
            'output_file': self.hdfs_path,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }
