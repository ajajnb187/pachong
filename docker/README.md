# 福州旅游大数据分析系统 - Docker部署指南

## 系统架构

本系统基于Hadoop和Hive构建，包含以下组件：

- **Hadoop 3.2.1**: 分布式文件系统（HDFS）用于存储海量旅游数据
- **Hive 2.3.2**: 数据仓库工具，支持SQL查询和分析
- **MySQL 5.7**: Hive元数据存储（Metastore）
- **Redis 7**: 缓存服务，提升查询性能
- **MySQL 8.0**: 业务数据库（可选，用于Flask应用）

## 版本兼容性说明

✅ **已验证的组件版本组合**：
- Hadoop 3.2.1 + Hive 2.3.2 + MySQL 5.7 (Metastore)
- 使用 `bde2020` 官方Docker镜像，经过大规模生产环境验证
- 所有配置已优化，避免常见的版本冲突问题

## 快速启动

### 1. 一键启动所有服务

```bash
cd docker
docker-compose up -d
```

### 2. 查看服务状态

```bash
docker-compose ps
```

所有服务应显示为 `Up` 状态。

### 3. 访问Web界面

- **Hadoop NameNode**: http://localhost:9870
- **Hadoop DataNode**: http://localhost:9864
- **HiveServer2 Web UI**: http://localhost:10002

## 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| NameNode Web UI | 9870 | HDFS管理界面 |
| NameNode RPC | 9000 | HDFS文件系统访问 |
| DataNode Web UI | 9864 | 数据节点状态 |
| HiveServer2 Thrift | 10000 | Hive JDBC/Beeline连接 |
| HiveServer2 Web UI | 10002 | Hive服务状态 |
| Hive Metastore | 9083 | 元数据服务 |
| Hive Metastore DB | 3307 | MySQL元数据库 |
| Redis | 6379 | 缓存服务（密码：redis123456） |
| MySQL业务库 | 3306 | Flask应用数据库 |

## 数据上传流程

### 自动上传（推荐）

爬虫脚本会自动将数据上传到HDFS：

```python
# 在 tourism-flask/tasks/crawl_task_v2.py 中
# 数据会自动上传到：
# /tourism/data/spots/dt=20251213_153045/
# /tourism/data/reviews/dt=20251213_153045/
```

### 手动上传

```bash
# 复制本地文件到Docker容器
docker cp your_data.jsonl namenode:/tmp/

# 进入容器
docker exec -it namenode bash

# 上传到HDFS
hdfs dfs -mkdir -p /tourism/data/spots/dt=20251213_153045
hdfs dfs -put /tmp/your_data.jsonl /tourism/data/spots/dt=20251213_153045/

# 修复分区（让Hive发现新数据）
docker exec -it hive-server bash
/opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -n root -e "
USE tourism_db;
MSCK REPAIR TABLE scenic_spots;
MSCK REPAIR TABLE fuzhou_reviews;
"
```

## Hive查询示例

### 连接到Hive

```bash
docker exec -it hive-server bash
/opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -n root
```

### 常用查询

```sql
-- 切换到旅游数据库
USE tourism_db;

-- 查看所有表
SHOW TABLES;

-- 查看分区
SHOW PARTITIONS scenic_spots;
SHOW PARTITIONS fuzhou_reviews;

-- 查询最新景点数据
SELECT * FROM scenic_spots_latest LIMIT 10;

-- 查询所有评论
SELECT * FROM fuzhou_reviews_all LIMIT 10;

-- 景点评分排行
SELECT scenic_spot, AVG(comment_score) as avg_score, COUNT(*) as review_count
FROM scenic_spots_latest
GROUP BY scenic_spot
ORDER BY avg_score DESC
LIMIT 10;

-- 查看数据统计
SELECT * FROM partition_stats ORDER BY partition_date DESC;
```

## 数据分析场景

### 1. 热门景点分析
```sql
SELECT scenic_spot, heat_score, comment_score, sight_level
FROM scenic_spots_latest
WHERE city = '福州'
ORDER BY heat_score DESC
LIMIT 20;
```

### 2. 游客评价分析
```sql
SELECT 
    scenic_spot,
    AVG(rating) as avg_rating,
    COUNT(*) as total_reviews,
    COUNT(DISTINCT visitor_name) as unique_visitors
FROM fuzhou_reviews_all
GROUP BY scenic_spot
ORDER BY avg_rating DESC, total_reviews DESC;
```

### 3. 季节性趋势分析
```sql
SELECT 
    SUBSTR(travel_date, 1, 7) as month,
    COUNT(*) as visit_count
FROM fuzhou_reviews_all
WHERE travel_date IS NOT NULL
GROUP BY SUBSTR(travel_date, 1, 7)
ORDER BY month;
```

## 故障排查

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs

# 查看特定服务日志
docker-compose logs namenode
docker-compose logs hive-server
docker-compose logs hive-metastore
```

### 常见问题

**1. Hive表初始化失败**
```bash
# 手动初始化
docker exec -it hive-server bash /opt/init-hive-tables.sh
```

**2. 无法连接到HiveServer2**
```bash
# 检查服务状态
docker exec -it hive-server netstat -tuln | grep 10000

# 重启Hive服务
docker-compose restart hive-server
```

**3. 数据上传后查询不到**
```bash
# 修复分区
docker exec -it hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -n root -e "
USE tourism_db;
MSCK REPAIR TABLE scenic_spots;
MSCK REPAIR TABLE fuzhou_reviews;
"
```

**4. HDFS空间不足**
```bash
# 查看HDFS使用情况
docker exec -it namenode hdfs dfsadmin -report

# 删除旧分区数据
docker exec -it namenode hdfs dfs -rm -r /tourism/data/reviews/dt=20251201_*
```

## 停止和清理

### 停止服务
```bash
docker-compose stop
```

### 完全清理（包括数据）
```bash
docker-compose down -v
```

### 重新部署
```bash
docker-compose down
docker-compose up -d
```

## 性能优化建议

1. **分区策略**: 数据已按时间戳分区，查询时尽量使用分区字段过滤
2. **数据格式**: 使用JSON格式存储，便于灵活查询
3. **缓存使用**: Redis已配置，可在Flask应用中缓存热点查询
4. **资源限制**: 根据机器配置调整 docker-compose.yml 中的资源限制

## 数据备份

```bash
# 备份HDFS数据
docker exec namenode hdfs dfs -get /tourism /backup/tourism-data

# 备份Hive元数据
docker exec hive-metastore-db mysqldump -uroot -proot123456 metastore > metastore_backup.sql
```

## 联系与支持

遇到问题请检查：
1. Docker和Docker Compose版本（推荐Docker 20+, Compose 1.29+）
2. 系统资源（至少4GB RAM，20GB磁盘空间）
3. 端口占用情况

---

**版本**: 1.0.0  
**更新时间**: 2024-12-13  
**兼容性**: Windows/Linux/macOS
