# Flask旅游数据爬虫服务

基于技术文档设计的Flask爬虫服务，支持携程、去哪儿、马蜂窝等多个旅游平台的数据爬取。

## 📋 功能特性

- ✅ **多数据源支持**：携程、去哪儿、马蜂窝
- ✅ **异步任务处理**：基于Celery的异步爬取
- ✅ **反爬虫策略**：随机UA、请求延迟、代理支持
- ✅ **数据清洗**：自动清洗和格式化爬取数据
- ✅ **HDFS存储**：数据自动存储到Hadoop HDFS
- ✅ **RESTful API**：完整的API接口供前端调用
- ✅ **任务管理**：启动、停止、查询任务状态

## 🛠️ 技术栈

- **Python 3.8+**
- **Flask 2.3** - Web框架
- **Celery 5.3** - 异步任务队列
- **Redis** - 消息代理
- **Requests + BeautifulSoup4** - 爬虫核心
- **fake-useragent** - UA随机化
- **SQLAlchemy** - ORM
- **MySQL** - 数据库
- **HDFS** - 大数据存储

## 📁 项目结构

```
tourism-flask/
├── app.py                    # Flask主应用
├── config.py                 # 配置文件
├── celery_worker.py         # Celery配置
├── requirements.txt          # 依赖包
├── .env.example             # 环境变量示例
├── crawlers/                # 爬虫模块
│   ├── __init__.py
│   ├── base_crawler.py      # 爬虫基类
│   ├── ctrip_crawler.py     # 携程爬虫
│   ├── qunar_crawler.py     # 去哪儿爬虫
│   └── mafengwo_crawler.py  # 马蜂窝爬虫
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── database.py          # 数据库连接
│   └── task.py             # 任务模型
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── logger.py           # 日志工具
│   ├── hdfs_client.py      # HDFS客户端
│   └── data_cleaner.py     # 数据清洗
├── tasks/                   # Celery任务
│   ├── __init__.py
│   └── crawl_task.py       # 爬取任务
└── logs/                    # 日志目录
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制`.env.example`为`.env`并修改配置：

```bash
cp .env.example .env
```

编辑`.env`文件，配置数据库、Redis、HDFS等信息：

```env
# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=tourism_db

# Redis配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# HDFS配置
HDFS_URL=http://localhost:9870
HDFS_USER=hadoop

# 代理配置（可选）
USE_PROXY=False
PROXY_SERVER=http://your-proxy:port
PROXY_USERNAME=your-username
PROXY_PASSWORD=your-password
```

### 3. 初始化数据库

确保MySQL已启动，数据库会自动创建表结构。

### 4. 启动服务

#### 方式一：分别启动（推荐开发环境）

```bash
# 终端1：启动Redis
redis-server

# 终端2：启动Celery Worker
celery -A celery_worker.celery_app worker --loglevel=info -P solo

# 终端3：启动Flask服务
python app.py
```

#### 方式二：后台启动（生产环境）

```bash
# 启动Redis
redis-server --daemonize yes

# 启动Celery Worker
nohup celery -A celery_worker.celery_app worker --loglevel=info > logs/celery.log 2>&1 &

# 启动Flask服务
nohup python app.py > logs/flask.log 2>&1 &
```

### 5. 验证服务

访问：http://localhost:5000

应该看到：
```json
{
  "service": "Tourism Flask Crawler Service",
  "version": "1.0.0",
  "status": "running"
}
```

## 📡 API接口

### 1. 启动爬取任务

```http
POST /api/crawler/start
Content-Type: application/json

{
  "task_name": "爬取三坊七巷评价数据",
  "scenic_spot_name": "三坊七巷",
  "data_source": "ctrip",
  "target_count": 100,
  "data_type": "review"
}
```

**响应：**
```json
{
  "code": 200,
  "msg": "任务已启动",
  "data": {
    "task_id": 1,
    "celery_task_id": "xxxx-xxxx-xxxx",
    "status": "running",
    "create_time": "2024-12-10 22:30:00"
  }
}
```

### 2. 查询任务状态

```http
GET /api/crawler/status/{task_id}
```

### 3. 查询任务列表

```http
GET /api/crawler/tasks?page=1&page_size=10&status=running
```

### 4. 停止任务

```http
POST /api/crawler/stop
Content-Type: application/json

{
  "task_id": 1
}
```

### 5. 删除任务

```http
DELETE /api/crawler/task/{task_id}
```

### 6. 获取数据源列表

```http
GET /api/datasource/list
```

### 7. 获取景区列表

```http
GET /api/scenic/list
```

### 8. 获取系统状态

```http
GET /api/system/status
```

## 🎯 使用示例

### Python调用示例

```python
import requests

# 启动爬取任务
url = "http://localhost:5000/api/crawler/start"
data = {
    "task_name": "爬取三坊七巷评价",
    "scenic_spot_name": "三坊七巷",
    "data_source": "ctrip",
    "target_count": 50,
    "data_type": "review"
}

response = requests.post(url, json=data)
result = response.json()
print(result)

task_id = result['data']['task_id']

# 查询任务状态
import time
while True:
    status_url = f"http://localhost:5000/api/crawler/status/{task_id}"
    resp = requests.get(status_url)
    task = resp.json()['data']
    
    print(f"进度: {task['progress']}%, 状态: {task['status']}")
    
    if task['status'] in ['success', 'failed']:
        break
    
    time.sleep(2)
```

### JavaScript调用示例

```javascript
// 启动爬取任务
async function startCrawl() {
  const response = await fetch('http://localhost:5000/api/crawler/start', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      task_name: '爬取三坊七巷评价',
      scenic_spot_name: '三坊七巷',
      data_source: 'ctrip',
      target_count: 50,
      data_type: 'review'
    })
  });
  
  const result = await response.json();
  console.log(result);
  
  return result.data.task_id;
}

// 查询任务状态
async function checkTaskStatus(taskId) {
  const response = await fetch(`http://localhost:5000/api/crawler/status/${taskId}`);
  const result = await response.json();
  console.log(`进度: ${result.data.progress}%, 状态: ${result.data.status}`);
}
```

## ⚙️ 配置说明

### 景区配置

在`config.py`的`FUZHOU_SCENIC_SPOTS`中添加新景区：

```python
'景区名称': {
    'ctrip_id': '携程景区ID',
    'qunar_id': '去哪儿景区ID', 
    'mafengwo_id': '马蜂窝景区ID',
    'keywords': ['关键词1', '关键词2']
}
```

### 爬虫配置

- `CRAWLER_REQUEST_DELAY_MIN`: 最小请求延迟(秒)
- `CRAWLER_REQUEST_DELAY_MAX`: 最大请求延迟(秒)
- `CRAWLER_MAX_RETRIES`: 最大重试次数
- `CRAWLER_TIMEOUT`: 请求超时时间(秒)

### 代理配置

如果需要使用代理：

```env
USE_PROXY=True
PROXY_SERVER=http://proxy.example.com:8080
PROXY_USERNAME=your_username
PROXY_PASSWORD=your_password
PROXY_CHANGE_INTERVAL=5  # 每5次请求更换IP
```

## 📝 日志查看

```bash
# 查看Flask日志
tail -f logs/crawler_20241210.log

# 查看Celery日志
tail -f logs/celery.log
```

## ⚠️ 注意事项

1. **反爬虫**：请合理设置请求频率，避免对目标网站造成压力
2. **数据源**：携程等网站的HTML结构可能变化，需要及时调整选择器
3. **HDFS**：确保HDFS服务正常运行，否则数据无法保存
4. **代理**：如遇频繁封IP，建议使用代理池
5. **合规性**：遵守目标网站的robots.txt规则和服务条款

## 🐛 常见问题

### Q1: HDFS连接失败

```bash
# 检查HDFS是否启动
jps | grep NameNode

# 检查端口
netstat -an | grep 9870

# 配置.env中的HDFS_URL
HDFS_URL=http://localhost:9870
```

### Q2: Celery任务不执行

```bash
# 检查Redis是否启动
redis-cli ping

# 重启Celery Worker
pkill -f celery
celery -A celery_worker.celery_app worker --loglevel=info -P solo
```

### Q3: 爬虫被封禁

- 增加请求延迟
- 启用代理
- 更换UA
- 检查是否触发验证码

## 📞 技术支持

如有问题，请查看：
- 系统设计文档
- API接口文档
- 爬取实现指南

## 📄 许可证

本项目仅用于学习和研究目的。
