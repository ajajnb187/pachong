# 福州旅游景区数据分析与可视化系统 - Flask数据爬取API接口设计

## 一、Flask爬虫服务概述

### 1.1 服务职责
- 提供RESTful API接口供前端调用
- 接收爬取任务请求并异步执行
- 爬取福州旅游景区数据
- 数据清洗和格式化
- 将处理后的数据存储到Hadoop HDFS
- 更新MySQL中的任务状态

### 1.2 技术栈
- **Web框架**：Flask 2.x
- **异步任务**：Celery + Redis
- **爬虫框架**：Requests + BeautifulSoup4 / Scrapy
- **数据处理**：Pandas
- **HDFS客户端**：hdfs3 / PyWebHDFS
- **MySQL驱动**：PyMySQL + SQLAlchemy

### 1.3 服务端口
- **开发环境**：http://localhost:5000
- **生产环境**：http://your-server:5000

## 二、API接口设计

### 2.1 基础响应格式

所有接口统一返回格式：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {}
}
```

**状态码说明**：
- `200`：成功
- `400`：请求参数错误
- `401`：未授权
- `500`：服务器内部错误

### 2.2 爬取任务管理接口

#### 2.2.1 启动爬取任务

**接口地址**：`POST /api/crawler/start`

**接口描述**：启动一个新的爬取任务，异步执行数据爬取

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| task_name | string | 是 | 任务名称 | "爬取三坊七巷评价数据" |
| scenic_spot_name | string | 是 | 景区名称 | "三坊七巷" |
| data_source | string | 是 | 数据来源（ctrip/qunar/meituan） | "ctrip" |
| target_count | int | 是 | 目标爬取数量 | 500 |
| data_type | string | 是 | 数据类型（review-评价/info-基本信息/count-游客数量） | "review" |

**请求示例**：

```json
{
    "task_name": "爬取三坊七巷携程评价数据",
    "scenic_spot_name": "三坊七巷",
    "data_source": "ctrip",
    "target_count": 500,
    "data_type": "review"
}
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "任务已启动",
    "data": {
        "task_id": 1001,
        "celery_task_id": "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
        "status": "running",
        "create_time": "2024-12-10 22:30:00"
    }
}
```

---

#### 2.2.2 停止爬取任务

**接口地址**：`POST /api/crawler/stop`

**接口描述**：停止正在运行的爬取任务

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| task_id | int | 是 | 任务ID | 1001 |

**请求示例**：

```json
{
    "task_id": 1001
}
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "任务已停止",
    "data": {
        "task_id": 1001,
        "status": "stopped"
    }
}
```

---

#### 2.2.3 查询任务状态

**接口地址**：`GET /api/crawler/status/{task_id}`

**接口描述**：查询指定任务的状态和进度

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| task_id | int | 是 | 任务ID（路径参数） | 1001 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "task_id": 1001,
        "task_name": "爬取三坊七巷携程评价数据",
        "scenic_spot_name": "三坊七巷",
        "data_source": "ctrip",
        "target_count": 500,
        "actual_count": 320,
        "status": "running",
        "progress": 64,
        "start_time": "2024-12-10 22:30:00",
        "end_time": null,
        "hdfs_path": "/tourism/raw/20241210/ctrip_sanfangqixiang_1001.json",
        "error_msg": null
    }
}
```

**任务状态说明**：
- `pending`：等待中
- `running`：运行中
- `success`：成功
- `failed`：失败
- `stopped`：已停止

---

#### 2.2.4 查询任务列表

**接口地址**：`GET /api/crawler/tasks`

**接口描述**：分页查询爬取任务列表

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| page | int | 否 | 页码 | 1 |
| page_size | int | 否 | 每页数量 | 10 |
| status | string | 否 | 任务状态 | 全部 |
| scenic_spot_name | string | 否 | 景区名称 | 全部 |

**请求示例**：

```
GET /api/crawler/tasks?page=1&page_size=10&status=running
```

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "total": 50,
        "page": 1,
        "page_size": 10,
        "tasks": [
            {
                "task_id": 1001,
                "task_name": "爬取三坊七巷携程评价数据",
                "scenic_spot_name": "三坊七巷",
                "data_source": "ctrip",
                "target_count": 500,
                "actual_count": 320,
                "status": "running",
                "progress": 64,
                "start_time": "2024-12-10 22:30:00",
                "create_time": "2024-12-10 22:29:55"
            }
        ]
    }
}
```

---

#### 2.2.5 删除任务记录

**接口地址**：`DELETE /api/crawler/task/{task_id}`

**接口描述**：删除指定的任务记录（只能删除已完成或失败的任务）

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| task_id | int | 是 | 任务ID（路径参数） | 1001 |

**响应示例**：

```json
{
    "code": 200,
    "msg": "删除成功",
    "data": null
}
```

---

### 2.3 数据源管理接口

#### 2.3.1 获取数据源列表

**接口地址**：`GET /api/datasource/list`

**接口描述**：获取所有可用的数据源配置

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": [
        {
            "source_code": "ctrip",
            "source_name": "携程旅行",
            "base_url": "https://you.ctrip.com",
            "is_enabled": true
        },
        {
            "source_code": "qunar",
            "source_name": "去哪儿网",
            "base_url": "https://travel.qunar.com",
            "is_enabled": true
        },
        {
            "source_code": "meituan",
            "source_name": "美团旅游",
            "base_url": "https://www.meituan.com/tourism",
            "is_enabled": true
        }
    ]
}
```

---

### 2.4 景区管理接口

#### 2.4.1 获取景区列表

**接口地址**：`GET /api/scenic/list`

**接口描述**：获取福州所有支持爬取的景区列表

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": [
        {
            "spot_id": "fuzhou_sanfangqixiang",
            "spot_name": "三坊七巷",
            "spot_type": "历史文化",
            "supported_sources": ["ctrip", "qunar", "meituan"]
        },
        {
            "spot_id": "fuzhou_gushan",
            "spot_name": "鼓山",
            "spot_type": "自然风光",
            "supported_sources": ["ctrip", "qunar"]
        },
        {
            "spot_id": "fuzhou_pingtandao",
            "spot_name": "平潭岛",
            "spot_type": "海滨度假",
            "supported_sources": ["ctrip", "qunar", "meituan"]
        }
    ]
}
```

---

### 2.5 系统监控接口

#### 2.5.1 获取爬虫服务状态

**接口地址**：`GET /api/system/status`

**接口描述**：获取Flask爬虫服务的运行状态

**响应示例**：

```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "service_status": "running",
        "celery_status": "running",
        "redis_status": "connected",
        "hdfs_status": "connected",
        "mysql_status": "connected",
        "running_tasks": 3,
        "pending_tasks": 2,
        "today_completed_tasks": 15
    }
}
```

---

## 三、Celery异步任务设计

### 3.1 任务队列配置

```python
# celery_config.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'Asia/Shanghai'
```

### 3.2 爬取任务流程

```python
@celery.task(bind=True)
def crawl_scenic_data(self, task_id, scenic_spot_name, data_source, target_count, data_type):
    """
    异步爬取任务
    
    Args:
        task_id: 任务ID
        scenic_spot_name: 景区名称
        data_source: 数据来源
        target_count: 目标数量
        data_type: 数据类型
    """
    try:
        # 1. 更新任务状态为运行中
        update_task_status(task_id, 'running', progress=0)
        
        # 2. 初始化爬虫
        crawler = get_crawler(data_source, data_type)
        
        # 3. 执行爬取
        data_list = []
        for i, data in enumerate(crawler.crawl(scenic_spot_name, target_count)):
            data_list.append(data)
            
            # 更新进度
            progress = int((i + 1) / target_count * 100)
            update_task_status(task_id, 'running', progress=progress, actual_count=i+1)
            
            # 检查是否被取消
            if is_task_stopped(task_id):
                update_task_status(task_id, 'stopped')
                return
        
        # 4. 数据清洗
        cleaned_data = clean_data(data_list, data_type)
        
        # 5. 存储到HDFS
        hdfs_path = save_to_hdfs(cleaned_data, task_id, scenic_spot_name, data_source)
        
        # 6. 更新任务状态为成功
        update_task_status(task_id, 'success', progress=100, 
                          actual_count=len(cleaned_data), 
                          hdfs_path=hdfs_path)
        
    except Exception as e:
        # 更新任务状态为失败
        update_task_status(task_id, 'failed', error_msg=str(e))
        raise
```

---

## 四、数据爬取实现方案

### 4.1 携程旅行数据爬取

#### 4.1.1 景区评价数据

**目标网站**：https://you.ctrip.com/sight/fuzhou109/XXX.html

**爬取字段**：
- 评价ID
- 景区ID
- 游客昵称
- 评分（1-5分）
- 评价内容
- 评价图片
- 游玩日期
- 评价日期
- 有用数
- 游客等级
- 游客所在地

**反爬虫策略**：
1. 设置User-Agent
2. 设置Referer
3. 控制请求频率（每次请求间隔1-3秒）
4. 使用代理IP池（可选）
5. 处理动态加载内容

**实现代码结构**：

```python
class CtripReviewCrawler:
    def __init__(self):
        self.base_url = "https://you.ctrip.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://you.ctrip.com'
        }
        self.session = requests.Session()
    
    def crawl(self, scenic_spot_name, target_count):
        """爬取评价数据"""
        # 1. 搜索景区，获取景区ID
        spot_id = self.search_scenic_spot(scenic_spot_name)
        
        # 2. 分页爬取评价
        page = 1
        count = 0
        while count < target_count:
            reviews = self.crawl_reviews_page(spot_id, page)
            for review in reviews:
                yield review
                count += 1
                if count >= target_count:
                    break
            page += 1
            time.sleep(random.uniform(1, 3))  # 随机延迟
    
    def crawl_reviews_page(self, spot_id, page):
        """爬取单页评价"""
        url = f"{self.base_url}/sight/{spot_id}/reviews-p{page}.html"
        response = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        reviews = []
        # 解析评价数据
        # ...
        return reviews
```

---

### 4.2 去哪儿网数据爬取

**目标网站**：https://travel.qunar.com/p-XXX

**爬取策略**：类似携程，需要处理Ajax请求

---

### 4.3 美团旅游数据爬取

**目标网站**：https://www.meituan.com/tourism/

**爬取策略**：需要处理反爬虫机制，可能需要登录

---

## 五、数据清洗与格式化

### 5.1 评价数据清洗

```python
def clean_review_data(raw_data):
    """
    清洗评价数据
    
    Args:
        raw_data: 原始爬取数据
        
    Returns:
        cleaned_data: 清洗后的数据
    """
    cleaned_data = {
        'review_id': generate_uuid(),
        'spot_id': extract_spot_id(raw_data),
        'spot_name': clean_text(raw_data.get('spot_name')),
        'visitor_name': clean_text(raw_data.get('visitor_name')),
        'rating': validate_rating(raw_data.get('rating')),
        'review_content': clean_text(raw_data.get('review_content')),
        'review_images': json.dumps(raw_data.get('images', [])),
        'travel_date': parse_date(raw_data.get('travel_date')),
        'review_date': parse_date(raw_data.get('review_date')),
        'helpful_count': int(raw_data.get('helpful_count', 0)),
        'visitor_level': raw_data.get('visitor_level'),
        'visitor_location': clean_text(raw_data.get('visitor_location')),
        'data_source': raw_data.get('data_source'),
        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return cleaned_data
```

### 5.2 数据验证规则

- **评分**：必须在1-5之间
- **日期**：格式统一为YYYY-MM-DD
- **文本**：去除特殊字符，过滤敏感词
- **必填字段**：景区名称、评价内容不能为空

---

## 六、HDFS数据存储

### 6.1 存储格式

- **格式**：JSON Lines（每行一个JSON对象）
- **编码**：UTF-8
- **压缩**：可选gzip压缩

### 6.2 存储路径规则

```
/tourism/raw/{date}/{source}_{spot}_{task_id}.json
```

示例：
```
/tourism/raw/20241210/ctrip_sanfangqixiang_1001.json
```

### 6.3 存储代码示例

```python
from hdfs import InsecureClient

def save_to_hdfs(data_list, task_id, scenic_spot_name, data_source):
    """
    保存数据到HDFS
    
    Args:
        data_list: 数据列表
        task_id: 任务ID
        scenic_spot_name: 景区名称
        data_source: 数据来源
        
    Returns:
        hdfs_path: HDFS存储路径
    """
    # 连接HDFS
    client = InsecureClient('http://localhost:9870', user='hadoop')
    
    # 生成文件路径
    date_str = datetime.now().strftime('%Y%m%d')
    spot_code = pinyin_convert(scenic_spot_name)
    filename = f"{data_source}_{spot_code}_{task_id}.json"
    hdfs_path = f"/tourism/raw/{date_str}/{filename}"
    
    # 转换为JSON Lines格式
    json_lines = '\n'.join([json.dumps(item, ensure_ascii=False) for item in data_list])
    
    # 写入HDFS
    with client.write(hdfs_path, encoding='utf-8') as writer:
        writer.write(json_lines)
    
    return hdfs_path
```

---

## 七、错误处理

### 7.1 常见错误及处理

| 错误类型 | 处理方式 |
|---------|---------|
| 网络超时 | 重试3次，每次间隔5秒 |
| 404错误 | 记录日志，跳过该条数据 |
| 反爬虫检测 | 更换User-Agent，增加延迟 |
| HDFS连接失败 | 重试连接，失败则回滚任务 |
| 数据格式错误 | 记录错误日志，跳过该条数据 |

### 7.2 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/crawler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

---

## 八、接口调用示例

### 8.1 Python调用示例

```python
import requests

# 启动爬取任务
url = "http://localhost:5000/api/crawler/start"
data = {
    "task_name": "爬取三坊七巷携程评价数据",
    "scenic_spot_name": "三坊七巷",
    "data_source": "ctrip",
    "target_count": 500,
    "data_type": "review"
}
response = requests.post(url, json=data)
result = response.json()
task_id = result['data']['task_id']

# 查询任务状态
status_url = f"http://localhost:5000/api/crawler/status/{task_id}"
response = requests.get(status_url)
print(response.json())
```

### 8.2 JavaScript (Vue) 调用示例

```javascript
// 启动爬取任务
async startCrawl() {
  try {
    const response = await axios.post('/api/crawler/start', {
      task_name: '爬取三坊七巷携程评价数据',
      scenic_spot_name: '三坊七巷',
      data_source: 'ctrip',
      target_count: 500,
      data_type: 'review'
    });
    
    if (response.data.code === 200) {
      this.$message.success('任务已启动');
      this.taskId = response.data.data.task_id;
      // 定时查询状态
      this.startPolling();
    }
  } catch (error) {
    this.$message.error('启动失败：' + error.message);
  }
}

// 定时查询任务状态
startPolling() {
  this.timer = setInterval(async () => {
    const response = await axios.get(`/api/crawler/status/${this.taskId}`);
    this.taskStatus = response.data.data;
    
    if (this.taskStatus.status === 'success' || 
        this.taskStatus.status === 'failed') {
      clearInterval(this.timer);
    }
  }, 2000);  // 每2秒查询一次
}
```

---

**文档版本**：V1.0  
**编写日期**：2024-12-10  
**注意**：由于无法实时搜索网页，以上爬取策略基于常见的旅游网站结构设计。实际开发时需要根据目标网站的最新结构调整爬虫代码。
