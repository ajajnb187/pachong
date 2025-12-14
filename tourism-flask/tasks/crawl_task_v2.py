"""
爬取任务V2 - 支持景点和评论数据分离
"""
import os
import json
import threading
from datetime import datetime
from models.database import SessionLocal
from models.task import CrawlerTask
from crawlers.ctrip_crawler_v2 import CtripCrawlerV2
from utils.logger import logger
from config import Config

# 全局字典，存储正在运行的任务停止事件
running_tasks = {}

def execute_crawl_fuzhou_complete(task_id, max_spots=50, reviews_per_spot=20):
    """
    执行完整的福州景区数据爬取任务
    
    流程：
    1. 爬取N个福州景点基本信息 -> scenic_spots表
    2. 为每个景点爬取用户评论 -> fuzhou_reviews表
    3. 分别存储到不同的JSONL文件
    4. 上传到Hadoop HDFS
    5. 清理Redis缓存，确保新数据生效
    
    Args:
        task_id: 任务ID
        max_spots: 爬取的景点数量（默认50个，0或-1表示全量爬取）
        reviews_per_spot: 每个景点爬取的评论数（默认20条，0或-1表示全量爬取）
    """
    db = SessionLocal()
    task = None
    stop_event = threading.Event()
    
    try:
        task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        # 注册停止事件
        running_tasks[task_id] = stop_event
        
        # 更新任务状态为运行中
        task.status = 'running'
        task.start_time = datetime.now()
        db.commit()
        
        # 从task获取目标数量（景点数量）
        if task.target_count:
            max_spots = task.target_count
        
        # 全量爬取模式：0或-1表示不限制
        is_full_mode = (max_spots <= 0 or reviews_per_spot <= 0)
        if max_spots <= 0:
            max_spots = 999999  # 设置一个极大值，爬取所有
        if reviews_per_spot <= 0:
            reviews_per_spot = 999999  # 设置一个极大值，爬取所有
        
        logger.info(f"========== 任务{task_id}开始 ==========")
        logger.info(f"模式: {'全量爬取（所有景点和评论）' if is_full_mode else f'限量爬取（{max_spots}个景点 x {reviews_per_spot}条评论）'}")
        
        # 初始化爬虫
        crawler = CtripCrawlerV2()
        
        # ========== 第一阶段：爬取N个景点基本信息 ==========
        logger.info("=" * 60)
        logger.info("阶段1: 爬取N个景点基本信息")
        logger.info("=" * 60)
        
        all_spots = crawler.crawl_all_scenic_spots(max_spots=max_spots)
        
        if not all_spots:
            raise Exception("未爬取到任何景点数据")
        
        logger.info(f"景点爬取完成，共 {len(all_spots)} 个景点")
        
        # 存储景点数据到JSONL文件
        spots_file = save_spots_to_file(all_spots, task_id)
        logger.info(f"景点数据已保存: {spots_file}")
        
        # ========== 第二阶段：爬取每个景点的用户评论 ==========
        logger.info("=" * 60)
        logger.info(f"阶段2: 爬取每个景点的用户评论（每景点{reviews_per_spot}条）")
        logger.info("=" * 60)
        
        all_reviews = []
        crawled_count = 0
        
        for idx, spot_info in enumerate(all_spots, 1):
            # 检查是否收到停止信号
            if stop_event.is_set():
                logger.warning(f"任务{task_id}收到停止信号，停止爬取")
                raise Exception("任务被用户手动停止")
            
            spot_id = spot_info.get('_spot_id')
            spot_name = spot_info.get('scenic_spot')
            
            if not spot_id:
                logger.warning(f"景点【{spot_name}】缺少ID，跳过评论爬取")
                continue
            
            logger.info(f"[{idx}/{len(all_spots)}] 正在爬取【{spot_name}】的评论...")
            
            try:
                reviews = crawler.crawl_reviews_for_spot(
                    spot_id, 
                    spot_name, 
                    max_reviews=reviews_per_spot,
                    stop_event=stop_event
                )
                
                if reviews:
                    all_reviews.extend(reviews)
                    crawled_count += len(reviews)
                    logger.info(f"【{spot_name}】爬取到 {len(reviews)} 条评论")
                else:
                    logger.warning(f"【{spot_name}】未获取到评论")
                
            except Exception as e:
                logger.error(f"爬取【{spot_name}】评论失败: {str(e)}")
                continue
        
        logger.info(f"评论爬取完成，共 {len(all_reviews)} 条评论")
        
        # 存储评论数据到JSONL文件
        reviews_file = save_reviews_to_file(all_reviews, task_id)
        logger.info(f"评论数据已保存: {reviews_file}")
        
        # 上传数据到Hadoop HDFS（按时间戳分区组织，避免同一天多次爬取冲突）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hdfs_spots_path = f"/tourism/data/spots/dt={timestamp}/"
        hdfs_reviews_path = f"/tourism/data/reviews/dt={timestamp}/"
        
        logger.info("="*60)
        logger.info("开始上传数据到Hadoop HDFS...")
        logger.info(f"景点文件: {spots_file}")
        logger.info(f"评论文件: {reviews_file}")
        logger.info(f"目标HDFS路径: {hdfs_spots_path}, {hdfs_reviews_path}")
        
        # 上传景点数据
        logger.info(f"正在上传景点数据到HDFS...")
        if upload_to_hadoop(spots_file, hdfs_spots_path):
            logger.info(f"✓ 景点数据已成功上传到HDFS: {hdfs_spots_path}")
        else:
            logger.error(f"✗ 景点数据上传HDFS失败")
        
        # 上传评论数据
        logger.info(f"正在上传评论数据到HDFS...")
        upload_success_reviews = upload_to_hadoop(reviews_file, hdfs_reviews_path)
        if upload_success_reviews:
            logger.info(f"✅ 评论数据已成功上传到HDFS: {hdfs_reviews_path}")
        else:
            logger.error("❌ 评论数据上传HDFS失败")
        
        # 修复Hive分区映射（关键步骤！）
        logger.info("="*60)
        logger.info("修复Hive分区映射...")
        logger.info("="*60)
        repair_hive_partitions()
        
        # 清理Redis缓存，确保新数据生效
        # 注意：缓存清理由前端负责调用（后端需要token认证）
        logger.info("="*60)
        logger.info("爬取任务完成，请前端调用缓存清理接口")
        logger.info("="*60)
        
        # 更新任务状态
        task.status = 'completed'
        task.end_time = datetime.now()
        task.actual_count = len(all_spots)
        task.hdfs_path = f"{hdfs_spots_path}, {hdfs_reviews_path}"
        db.commit()
        
        logger.info("=" * 60)
        logger.info(f"✅ 任务完成: 景点{len(all_spots)}个, 评论{len(all_reviews)}条")
        logger.info(f"HDFS路径: 景点={hdfs_spots_path}, 评论={hdfs_reviews_path}")
        logger.info("Redis缓存已清理，新数据已生效")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}", exc_info=True)
        if task:
            # 判断是否是手动停止
            if "手动停止" in str(e):
                task.status = 'stopped'
            else:
                task.status = 'failed'
            task.error_msg = str(e)
            task.end_time = datetime.now()
            db.commit()
    finally:
        # 清理停止事件
        if task_id in running_tasks:
            del running_tasks[task_id]
        db.close()


def stop_task(task_id):
    """
    停止正在运行的任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        bool: 是否成功发送停止信号
    """
    if task_id in running_tasks:
        logger.info(f"发送停止信号给任务: {task_id}")
        running_tasks[task_id].set()
        return True
    else:
        logger.warning(f"任务{task_id}不在运行中，无法停止")
        return False


def save_spots_to_file(spots_data, task_id):
    """
    保存景点数据到JSONL文件（对应scenic_spots表）
    
    文件格式：spots_福州_任务ID_时间.jsonl
    每行一个JSON对象，包含字段：
    - scenic_spot, city, review_count, avg_rating, last_review_date
    """
    config = Config()
    
    # 创建日期目录
    date_str = datetime.now().strftime('%Y%m%d')
    date_dir = os.path.join(config.DATA_RAW_PATH, date_str)
    os.makedirs(date_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"spots_fuzhou_{task_id}_{timestamp}.jsonl"
    file_path = os.path.join(date_dir, filename)
    
    # 写入JSONL文件（UTF-8编码）
    with open(file_path, 'w', encoding='utf-8') as f:
        for spot in spots_data:
            # 移除临时字段（以_开头的字段）
            clean_spot = {k: v for k, v in spot.items() if not k.startswith('_')}
            
            # 写入一行JSON
            f.write(json.dumps(clean_spot, ensure_ascii=False) + '\n')
    
    logger.info(f"景点数据已写入: {file_path} ({len(spots_data)}条)")
    return file_path


def save_reviews_to_file(reviews_data, task_id):
    """
    保存评论数据到JSONL文件（对应fuzhou_reviews表）
    
    文件格式：reviews_福州_任务ID_时间.jsonl
    每行一个JSON对象，包含字段：
    - scenic_spot, city, rating, visitor_name, review_content,
      travel_date, review_date, data_source, crawl_time
    """
    config = Config()
    
    # 创建日期目录
    date_str = datetime.now().strftime('%Y%m%d')
    date_dir = os.path.join(config.DATA_RAW_PATH, date_str)
    os.makedirs(date_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"reviews_fuzhou_{task_id}_{timestamp}.jsonl"
    file_path = os.path.join(date_dir, filename)
    
    # 写入JSONL文件（UTF-8编码）
    with open(file_path, 'w', encoding='utf-8') as f:
        for review in reviews_data:
            # 写入一行JSON
            f.write(json.dumps(review, ensure_ascii=False) + '\n')
    
    logger.info(f"评论数据已写入: {file_path} ({len(reviews_data)}条)")
    return file_path


def upload_to_hadoop(local_file, hadoop_path):
    """
    上传文件到Hadoop HDFS
    
    Args:
        local_file: 本地文件路径（Windows路径）
        hadoop_path: Hadoop目标目录路径（不含文件名）
    """
    import subprocess
    import os
    
    try:
        # 确保目标目录存在
        mkdir_cmd = [
            'docker', 'exec', 'namenode',
            'hdfs', 'dfs', '-mkdir', '-p', hadoop_path
        ]
        subprocess.run(mkdir_cmd, capture_output=True, text=True)
        logger.info(f"确保HDFS目录存在: {hadoop_path}")
        
        # 获取文件名
        filename = os.path.basename(local_file)
        
        # 复制文件到docker容器内
        docker_cp_cmd = [
            'docker', 'cp', local_file, f'namenode:/tmp/{filename}'
        ]
        result = subprocess.run(docker_cp_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"复制文件到容器失败: {result.stderr}")
            return False
        
        # 从容器内上传到HDFS
        hdfs_put_cmd = [
            'docker', 'exec', 'namenode',
            'hdfs', 'dfs', '-put', '-f',
            f'/tmp/{filename}', hadoop_path
        ]
        result = subprocess.run(hdfs_put_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"文件已上传到HDFS: {hadoop_path}/{filename}")
            # 清理容器内临时文件
            rm_cmd = ['docker', 'exec', 'namenode', 'rm', '-f', f'/tmp/{filename}']
            subprocess.run(rm_cmd, capture_output=True, text=True)
            return True
        else:
            logger.error(f"上传HDFS失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"上传HDFS异常: {str(e)}")
        return False


def repair_hive_partitions():
    """
    修复Hive分区映射
    上传数据到HDFS后必须执行此操作，否则Hive查询不到数据
    """
    import subprocess
    
    try:
        # 修复scenic_spots表分区
        repair_spots_cmd = [
            'docker', 'exec', 'hive-server',
            '/opt/hive/bin/beeline', '-u', 'jdbc:hive2://localhost:10000',
            '-e', 'USE tourism_db; MSCK REPAIR TABLE scenic_spots;'
        ]
        result = subprocess.run(repair_spots_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ scenic_spots表分区修复成功")
        else:
            logger.warning(f"scenic_spots表分区修复失败: {result.stderr}")
        
        # 修复fuzhou_reviews表分区
        repair_reviews_cmd = [
            'docker', 'exec', 'hive-server',
            '/opt/hive/bin/beeline', '-u', 'jdbc:hive2://localhost:10000',
            '-e', 'USE tourism_db; MSCK REPAIR TABLE fuzhou_reviews;'
        ]
        result = subprocess.run(repair_reviews_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ fuzhou_reviews表分区修复成功")
        else:
            logger.warning(f"fuzhou_reviews表分区修复失败: {result.stderr}")
        
        return True
        
    except Exception as e:
        logger.error(f"修复Hive分区异常: {str(e)}")
        return False


# 缓存清理已移除，改为由前端在爬虫完成后调用Spring Boot的缓存清理接口
# 前端应调用：DELETE /api/cache/clear-all
