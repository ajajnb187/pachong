# 福州旅游景区数据分析系统 - Docker一键部署指南

## 🎯 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   福州旅游景区数据分析系统                  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
   │  Flask  │        │ Spring  │        │  Hadoop │
   │  爬虫服务 │        │  Boot   │        │  + Hive │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
   │  MySQL  │        │  Redis  │        │  HDFS   │
   │  数据库  │        │  缓存   │        │  存储   │
   └─────────┘        └─────────┘        └─────────┘
```

## 📦 包含的服务

| 服务 | 端口 | 说明 |
|------|------|------|
| **MySQL** | 3306 | 用户数据、爬虫任务数据 |
| **Redis** | 6379 | SaToken会话存储 |
| **Hadoop NameNode** | 9870 (Web), 9000 (HDFS) | Hadoop主节点 |
| **Hadoop DataNode** | - | Hadoop数据节点 |
| **Hive Metastore** | 9083 | Hive元数据服务 |
| **HiveServer2** | 10000, 10002 (Web) | Hive查询服务 |
| **Flask爬虫** | 5000 | 数据采集服务 |
| **Celery Worker** | - | 异步爬虫任务 |
| **Spring Boot** | 8080 | 数据分析API服务 |

## 🚀 一键启动（Windows）

### 第一步：准备环境
1. 安装Docker Desktop
2. 确保Docker正在运行
3. 确保至少有10GB可用磁盘空间

### 第二步：一键启动
```bash
# 双击运行
一键启动.bat
```

或手动执行：
```bash
docker-compose up -d
```

## 📝 详细操作步骤

### 1. 启动所有服务
```bash
docker-compose up -d
```

等待3-5分钟，所有服务启动完成。

### 2. 查看服务状态
```bash
docker-compose ps
```

所有服务都应该显示`Up`状态。

### 3. 初始化HDFS目录
```bash
docker exec tourism-namenode bash /init-hdfs.sh
```

### 4. 初始化Hive表
```bash
docker exec -it tourism-hiveserver2 beeline -u jdbc:hive2://localhost:10000 -f /opt/hive_init.sql
```

### 5. 验证服务

#### 5.1 访问Spring Boot API文档
```
http://localhost:8080/doc.html
```

#### 5.2 测试Flask爬虫服务
```bash
curl http://localhost:5000/
```

#### 5.3 访问Hadoop Web UI
```
http://localhost:9870
```

## 🔍 第一次使用流程

### 步骤1：登录系统
```bash
# POST http://localhost:8080/api/auth/login
{
  "username": "admin",
  "password": "123456"
}
```

### 步骤2：启动爬虫任务
```bash
# POST http://localhost:5000/api/crawler/start
{
  "spot_name": "三坊七巷",
  "data_source": "ctrip",
  "target_count": 100,
  "data_type": "review"
}
```

### 步骤3：查看爬取进度
```bash
# GET http://localhost:5000/api/crawler/tasks
```

### 步骤4：验证数据已存入HDFS
```bash
docker exec tourism-namenode hdfs dfs -ls -R /tourism/raw
```

### 步骤5：在Hive中查询数据
```bash
docker exec -it tourism-hiveserver2 beeline -u jdbc:hive2://localhost:10000

# 执行SQL
> SELECT COUNT(*) FROM tourism_db.fuzhou_reviews;
> SELECT spot_name, COUNT(*) FROM tourism_db.fuzhou_reviews GROUP BY spot_name;
```

### 步骤6：调用Spring Boot分析API
```bash
# 数据概览
GET http://localhost:8080/api/analysis/overview

# 客流量统计
GET http://localhost:8080/api/analysis/visitor-count?spotId=三坊七巷&startDate=2024-01-01&endDate=2024-12-31

# 评价统计
GET http://localhost:8080/api/analysis/review-stats?spotId=三坊七巷
```

## 📊 数据流程

```
1. Flask爬虫爬取携程数据
        ↓
2. 数据清洗并保存为JSONL格式
        ↓
3. 写入HDFS: /tourism/raw/
        ↓
4. Hive外部表自动读取HDFS数据
        ↓
5. Spring Boot通过Hive JDBC查询分析
        ↓
6. 返回分析结果给前端
```

## 🗂️ Hive表结构

### 1. 景区信息表
```sql
CREATE EXTERNAL TABLE fuzhou_scenic_spots (
    spot_id STRING,
    spot_name STRING,
    spot_type STRING,
    location STRING,
    address STRING,
    longitude DOUBLE,
    latitude DOUBLE,
    open_time STRING,
    ticket_price DOUBLE,
    description STRING,
    ...
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/tourism/raw/scenic_info/';
```

### 2. 评论数据表
```sql
CREATE EXTERNAL TABLE fuzhou_reviews (
    review_id STRING,
    spot_id STRING,
    spot_name STRING,
    visitor_name STRING,
    rating DOUBLE,
    review_content STRING,
    travel_date STRING,
    review_date STRING,
    ...
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION '/tourism/raw/';
```

## 🛠️ 常用命令

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f springboot-api
docker-compose logs -f flask-crawler
docker-compose logs -f hiveserver2
```

### 进入容器
```bash
# 进入Spring Boot容器
docker exec -it tourism-springboot bash

# 进入Flask容器
docker exec -it tourism-flask bash

# 进入Hive容器
docker exec -it tourism-hiveserver2 bash
```

### 重启服务
```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart springboot-api
```

### 停止服务
```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（慎用）
docker-compose down -v
```

## ⚠️ 常见问题

### 1. 端口被占用
```bash
# 修改docker-compose.yml中的端口映射
ports:
  - "8081:8080"  # 改为其他端口
```

### 2. HDFS连接失败
```bash
# 检查HDFS是否启动
docker exec tourism-namenode hdfs dfsadmin -report

# 重新创建HDFS目录
docker exec tourism-namenode bash /init-hdfs.sh
```

### 3. Hive查询失败
```bash
# 检查HiveServer2是否启动
docker exec tourism-hiveserver2 beeline -u jdbc:hive2://localhost:10000 -e "show databases;"

# 重新初始化Hive表
docker exec -it tourism-hiveserver2 beeline -u jdbc:hive2://localhost:10000 -f /opt/hive_init.sql
```

### 4. MySQL连接失败
```bash
# 检查MySQL是否启动
docker exec tourism-mysql mysql -uroot -proot123456 -e "SELECT 1;"

# 重新初始化MySQL
docker exec -i tourism-mysql mysql -uroot -proot123456 < tourism-springboot/src/main/resources/sql/01_mysql_init.sql
```

## 💡 性能优化建议

### 1. 调整Docker资源
Docker Desktop -> Settings -> Resources
- CPU: 至少4核
- Memory: 至少8GB
- Disk: 至少20GB

### 2. Hive查询优化
```sql
-- 使用分区表
CREATE TABLE partitioned_reviews
PARTITIONED BY (dt STRING)
AS SELECT * FROM fuzhou_reviews;

-- 开启CBO优化
SET hive.cbo.enable=true;
SET hive.compute.query.using.stats=true;
```

### 3. HDFS副本数设置
```bash
# 单节点环境设置副本数为1
hdfs dfs -setrep 1 /tourism/raw
```

## 📚 参考文档

- Docker Compose: https://docs.docker.com/compose/
- Hadoop: https://hadoop.apache.org/docs/
- Hive: https://hive.apache.org/
- Spring Boot: https://spring.io/projects/spring-boot
- Flask: https://flask.palletsprojects.com/

## ✅ 验证清单

- [ ] Docker Desktop已启动
- [ ] 所有容器状态为Up
- [ ] HDFS Web UI可访问 (http://localhost:9870)
- [ ] Spring Boot API文档可访问 (http://localhost:8080/doc.html)
- [ ] Flask爬虫服务可访问 (http://localhost:5000)
- [ ] MySQL可连接
- [ ] Redis可连接
- [ ] Hive可查询
- [ ] HDFS目录已创建

---

**第一次操作总结：**
1. 运行`一键启动.bat`
2. 等待5分钟让所有服务启动
3. 初始化HDFS和Hive
4. 登录系统，启动爬虫
5. 等待数据爬取完成
6. 在Hive中验证数据
7. 调用分析API测试

**就这么简单！** 🎉
