# 福州旅游大数据分析系统 - 部署说明

## 🎯 一键部署

运行部署脚本：
```bash
cd docker
deploy.bat
```

## ✅ 自动完成的配置

部署脚本会自动完成以下配置，**无需手动干预**：

### 1. Hive表自动创建
- ✅ `scenic_spots` - 景区信息表（分区表）
- ✅ `fuzhou_reviews` - 评论数据表（分区表，使用正确的JsonSerDe）

### 2. VIEW视图自动创建
- ✅ `scenic_spots_latest` - 最新景区数据视图
- ✅ `fuzhou_reviews_latest` - 最新评论数据视图
- ✅ `fuzhou_reviews_all` - 全量评论数据视图
- ✅ `partition_stats` - 分区统计视图

### 3. 配置优化
- ✅ Hive本地执行模式（无需YARN）
- ✅ Fetch Task优化（避免MapReduce）
- ✅ JsonSerDe正确配置

## 📊 部署后验证

### 验证Hive表和VIEW
```bash
# 查看所有表和视图
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW TABLES IN tourism_db"

# 查看分区
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW PARTITIONS tourism_db.scenic_spots"
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW PARTITIONS tourism_db.fuzhou_reviews"

# 验证VIEW可用
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SELECT COUNT(*) FROM tourism_db.scenic_spots_latest"
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SELECT COUNT(*) FROM tourism_db.fuzhou_reviews_latest"
```

## 🚀 数据上传流程

### 1. 运行爬虫上传数据
```bash
cd tourism-flask
python app.py
```

爬虫会自动：
- 爬取福州景区数据
- 上传到HDFS分区目录
- 自动注册分区到Hive

### 2. 验证数据
```bash
# 查看景区数据
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SELECT COUNT(*) FROM tourism_db.scenic_spots_latest"

# 查看评论数据
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SELECT COUNT(*) FROM tourism_db.fuzhou_reviews_latest"
```

### 3. 启动后端服务
```bash
cd tourism-springboot
mvn spring-boot:run
```

### 4. 启动前端
```bash
cd tourism-vue
npm run dev
```

## 🔧 故障排查

### 问题：VIEW不存在
**原因**：init-hiveserver.sh未执行hive-init-partitioned.sql

**解决**：
```bash
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -f /opt/hive-init-partitioned.sql
```

### 问题：评论表返回空数据
**原因**：JsonSerDe配置错误

**解决**：
```bash
# 重建评论表
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "DROP TABLE tourism_db.fuzhou_reviews"
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "CREATE EXTERNAL TABLE tourism_db.fuzhou_reviews (scenic_spot STRING, city STRING, rating DOUBLE, visitor_name STRING, review_content STRING, travel_date STRING, review_date STRING, visitor_location STRING, ip_location STRING, data_source STRING, crawl_time STRING) PARTITIONED BY (dt STRING) ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe' STORED AS TEXTFILE LOCATION '/tourism/data/reviews/'"
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "MSCK REPAIR TABLE tourism_db.fuzhou_reviews"
```

### 问题：MapReduce错误
**原因**：Hive配置未生效

**解决**：已在hadoop.env中配置，重启容器：
```bash
docker-compose restart hive-server
```

## 📝 关键文件说明

| 文件 | 作用 |
|------|------|
| `init-hive-tables.sh` | 创建基础分区表 |
| `hive-init-partitioned.sql` | 创建VIEW视图和分区统计 |
| `init-hiveserver.sh` | 启动HiveServer2并执行初始化脚本 |
| `docker-compose.yml` | Docker服务编排，挂载初始化脚本 |
| `hadoop.env` | Hive优化配置（本地模式、Fetch Task） |

## ⚠️ 重要提示

1. **VIEW已自动创建**：部署完成后，所有VIEW视图已自动创建，无需手动执行SQL
2. **JsonSerDe已修复**：评论表使用正确的`org.apache.hive.hcatalog.data.JsonSerDe`
3. **分区自动发现**：爬虫上传数据后会自动执行`MSCK REPAIR TABLE`注册分区
4. **无MapReduce错误**：已配置本地模式和Fetch Task优化，避免MapReduce任务

## 🎉 部署成功标志

当看到以下输出时，表示部署成功：

```
HiveServer2启动完成，保持运行...
```

此时可以验证：
```bash
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW TABLES IN tourism_db"
```

应该看到6个表/视图：
- fuzhou_reviews
- fuzhou_reviews_all
- fuzhou_reviews_latest
- partition_stats
- scenic_spots
- scenic_spots_latest
