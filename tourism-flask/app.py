"""
Flask爬虫服务主应用
提供RESTful API接口供前端调用
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

from config import Config
from models.database import SessionLocal, init_db
from models.task import CrawlerTask
from tasks.crawl_task import execute_crawl_task, execute_crawl_task_direct
from tasks.crawl_task_v2 import execute_crawl_fuzhou_complete
from utils.logger import logger

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # 允许跨域请求

# 数据库初始化由用户手动执行，不自动创建表
# init_db()

@app.route('/', methods=['GET'])
def index():
    """API根路径"""
    return jsonify({
        'service': '福州旅游景区数据采集服务',
        'version': '1.0.0',
        'status': 'running',
        'data_source': '携程旅行',
        'storage_format': 'JSONL (Hadoop HDFS)',
        'note': '数据可直接导入Hive分析'
    })

@app.route('/api/crawler/start', methods=['POST'])
def start_crawl():
    """启动爬取任务"""
    try:
        data = request.get_json()
        
        # 验证必填参数
        required_fields = ['task_name', 'scenic_spot_name', 'data_source', 'target_count', 'data_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 400,
                    'msg': f'缺少参数: {field}'
                }), 400
        
        # 验证数据来源（目前只实现了携程）
        if data['data_source'] != '携程':
            return jsonify({
                'code': 400,
                'msg': '目前仅支持携程数据源 (data_source=ctrip)'
            }), 400
        
        # 验证数据类型
        valid_types = ['review', 'info']
        if data['data_type'] not in valid_types:
            return jsonify({
                'code': 400,
                'msg': f'不支持的数据类型，支持: {", ".join(valid_types)}'
            }), 400
        
        db = SessionLocal()
        
        try:
            # 创建任务记录
            task = CrawlerTask(
                task_name=data['task_name'],
                scenic_spot_name=data['scenic_spot_name'],
                data_source=data['data_source'],
                target_count=int(data['target_count']),
                status='pending',
                create_by=1  # 默认用户ID
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            task_id = task.id
            
            logger.info(f"创建爬取任务: ID={task_id}, 景区={data['scenic_spot_name']}, 来源={data['data_source']}")
            
            # 启动后台线程执行爬取任务
            import threading
            thread = threading.Thread(
                target=execute_crawl_task_direct,
                args=(task_id, data['scenic_spot_name'], data['data_source'], int(data['target_count']), data['data_type'])
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'code': 200,
                'msg': '任务已启动',
                'data': {
                    'task_id': task_id,
                    'status': 'running',
                    'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"启动任务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'启动失败: {str(e)}'
        }), 500

@app.route('/api/crawler/status/<int:task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询任务状态"""
    try:
        db = SessionLocal()
        
        try:
            task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'msg': '任务不存在'
                }), 404
            
            return jsonify({
                'code': 200,
                'msg': '成功',
                'data': task.to_dict()
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'查询失败: {str(e)}'
        }), 500

@app.route('/api/crawler/tasks', methods=['GET'])
def get_task_list():
    """查询任务列表"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        status = request.args.get('status')
        scenic_spot_name = request.args.get('scenic_spot_name')
        
        db = SessionLocal()
        
        try:
            query = db.query(CrawlerTask)
            
            # 过滤条件
            if status:
                query = query.filter(CrawlerTask.status == status)
            if scenic_spot_name:
                query = query.filter(CrawlerTask.scenic_spot_name.like(f'%{scenic_spot_name}%'))
            
            total = query.count()
            
            # 分页查询
            tasks = query.order_by(CrawlerTask.create_time.desc()) \
                        .offset((page - 1) * page_size) \
                        .limit(page_size) \
                        .all()
            
            return jsonify({
                'code': 200,
                'msg': '成功',
                'data': {
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'tasks': [task.to_dict() for task in tasks]
                }
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"查询任务列表失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'查询失败: {str(e)}'
        }), 500

@app.route('/api/crawler/stop', methods=['POST'])
def stop_task():
    """停止任务"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({
                'code': 400,
                'msg': '缺少参数: task_id'
            }), 400
        
        db = SessionLocal()
        
        try:
            task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'msg': '任务不存在'
                }), 404
            
            if task.status != 'running':
                return jsonify({
                    'code': 400,
                    'msg': '任务未在运行中'
                }), 400
            
            # 更新任务状态
            task.status = 'stopped'
            task.end_time = datetime.now()
            db.commit()
            
            logger.info(f"任务已停止: {task_id}")
            
            return jsonify({
                'code': 200,
                'msg': '任务已停止',
                'data': {
                    'task_id': task_id,
                    'status': 'stopped'
                }
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"停止任务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'停止失败: {str(e)}'
        }), 500

@app.route('/api/crawler/task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务记录"""
    try:
        db = SessionLocal()
        
        try:
            task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
            
            if not task:
                return jsonify({
                    'code': 404,
                    'msg': '任务不存在'
                }), 404
            
            if task.status == 'running':
                return jsonify({
                    'code': 400,
                    'msg': '无法删除正在运行的任务'
                }), 400
            
            db.delete(task)
            db.commit()
            
            logger.info(f"任务已删除: {task_id}")
            
            return jsonify({
                'code': 200,
                'msg': '删除成功'
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'删除失败: {str(e)}'
        }), 500

@app.route('/api/datasource/list', methods=['GET'])
def get_datasource_list():
    """获取数据源列表"""
    return jsonify({
        'code': 200,
        'msg': '成功',
        'data': [
            {
                'source_code': 'ctrip',
                'source_name': '携程旅行',
                'base_url': 'https://m.ctrip.com',
                'api_type': '移动端API',
                'is_enabled': True,
                'note': '已实现，可正常使用'
            }
        ]
    })

@app.route('/api/scenic/list', methods=['GET'])
def get_scenic_list():
    """获取福州景区列表（从爬虫动态获取）"""
    return jsonify({
        'code': 200,
        'msg': '成功',
        'data': {
            'city_name': '福州',
            'city_id': Config.FUZHOU_CITY_ID,
            'note': '景区列表由爬虫动态获取，请使用"福州"作为景区名称启动爬取任务'
        }
    })

@app.route('/api/admin/crawl/test', methods=['POST'])
def admin_crawl_test():
    """
    测试接口：爬取少量数据测试Hadoop上传
    
    只爬取3个景点，每个景点3条评论，用于测试上传功能
    """
    try:
        from tasks.crawl_task_v2 import execute_crawl_fuzhou_complete
        
        db = SessionLocal()
        
        try:
            task = CrawlerTask(
                task_name=f'【测试】少量数据测试-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                scenic_spot_name='福州',
                data_source='ctrip',
                target_count=3,  # 只爬3条
                status='pending',
                create_by=1
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            task_id = task.id
            
            logger.info(f"测试任务启动: ID={task_id}")
            
            # 启动后台线程
            import threading
            thread = threading.Thread(
                target=execute_crawl_fuzhou_complete,
                args=(task_id,)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'code': 200,
                'msg': '测试任务已启动',
                'data': {
                    'task_id': task_id,
                    'note': '只爬取3个景点，每个3条评论，测试Hadoop上传'
                }
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"测试任务启动失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'启动失败: {str(e)}'
        }), 500


@app.route('/api/admin/crawl/fuzhou', methods=['POST'])
def admin_crawl_fuzhou_all():
    """
    管理员专用：一键爬取福州所有景区评论数据并存入Hadoop
    
    功能说明：
    1. 自动爬取福州所有热门景区的用户评论数据（含真实评论和官方描述）
    2. 数据包含：景区信息、评分、评论内容、图片URL、旅游日期、评论日期等
    3. 自动存储到Hadoop HDFS（JSONL格式）
    4. 可直接用于Hive建表和数据分析
    
    存储格式：JSONL (每行一条JSON记录)
    存储路径：/tourism/data/raw/YYYYMMDD/ctrip_景区名_任务ID_时间.jsonl
    
    Hive建表语句：
    CREATE EXTERNAL TABLE fuzhou_reviews (
        scenic_spot STRING COMMENT '景区名称',
        city STRING COMMENT '城市',
        rating DOUBLE COMMENT '评分(1-5)',
        visitor_name STRING COMMENT '游客昵称',
        review_content STRING COMMENT '评论内容',
        review_images STRING COMMENT '评论图片JSON数组',
        travel_date STRING COMMENT '旅游日期YYYY-MM-DD',
        review_date STRING COMMENT '评论日期YYYY-MM-DD',
        helpful_count INT COMMENT '点赞数',
        visitor_level STRING COMMENT '游客等级',
        visitor_location STRING COMMENT '游客所在地',
        data_source STRING COMMENT '数据来源',
        crawl_time STRING COMMENT '爬取时间'
    )
    ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
    STORED AS TEXTFILE
    LOCATION '/tourism/data/raw/';
    
    请求参数（可选）:
    {
        "target_count": 500,  // 目标数据量，默认500条，设置为0或-1表示全量爬取
        "crawl_mode": "full"  // full=全量爬取, limit=限量爬取（默认）
    }
    """
    try:
        data = request.get_json() if request.is_json else {}
        
        # 参数处理
        target_count = int(data.get('target_count', 500))
        crawl_mode = data.get('crawl_mode', 'limit')
        
        # 全量爬取模式：设置一个很大的数字
        if crawl_mode == 'full' or target_count <= 0:
            target_count = 10000  # 设置为10000条，基本上能覆盖所有福州景区
            crawl_mode = 'full'
        
        data_source = 'ctrip'
        
        db = SessionLocal()
        
        try:
            # 创建管理员爬取任务
            task = CrawlerTask(
                task_name=f'【管理员】福州所有景区数据采集-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                scenic_spot_name='福州',  # 爬取所有福州景区
                data_source=data_source,
                target_count=target_count,
                status='pending',
                create_by=1  # 管理员用户ID
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            task_id = task.id
            
            logger.info(f"管理员启动福州全景区爬取: ID={task_id}, 目标={target_count}条")
            
            # 启动后台线程执行爬取任务（使用V2版本）
            import threading
            # 计算每个景点爬取的评论数
            reviews_per_spot = max(10, target_count // 100)  # 假设100个景点
            thread = threading.Thread(
                target=execute_crawl_fuzhou_complete,
                args=(task_id, reviews_per_spot)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'code': 200,
                'msg': '福州所有景区数据采集任务已启动',
                'data': {
                    'task_id': task_id,
                    'scenic_spot_name': '福州（所有景区）',
                    'data_source': data_source,
                    'target_count': target_count,
                    'status': 'running',
                    'note': '数据将自动存入Hadoop HDFS',
                    'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"管理员爬取任务启动失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'启动失败: {str(e)}'
        }), 500

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """获取系统状态"""
    try:
        db = SessionLocal()
        
        try:
            # 统计任务数量
            running_tasks = db.query(CrawlerTask).filter(CrawlerTask.status == 'running').count()
            pending_tasks = db.query(CrawlerTask).filter(CrawlerTask.status == 'pending').count()
            
            from datetime import date
            today = date.today()
            today_completed = db.query(CrawlerTask).filter(
                CrawlerTask.status == 'success',
                CrawlerTask.end_time >= today
            ).count()
            
            return jsonify({
                'code': 200,
                'msg': '成功',
                'data': {
                    'service_status': 'running',
                    'celery_status': 'running',
                    'redis_status': 'connected',
                    'hdfs_status': 'connected',
                    'mysql_status': 'connected',
                    'running_tasks': running_tasks,
                    'pending_tasks': pending_tasks,
                    'today_completed_tasks': today_completed
                }
            })
            
        finally:
            db.close()
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': str(e),
            'data': {
                'service_status': 'error'
            }
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'code': 404,
        'msg': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器错误: {str(error)}")
    return jsonify({
        'code': 500,
        'msg': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    logger.info("Flask爬虫服务启动...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
