# 福州旅游景区数据采集API使用说明

## 系统概述

本系统用于爬取福州所有景区的用户评论数据，并自动存储到Hadoop HDFS，供Hive分析使用。

- **数据源**：携程旅行（移动端API）
- **存储格式**：JSONL（每行一条JSON记录）
- **存储位置**：Hadoop HDFS `/tourism/data/raw/`
- **适用场景**：基于Hadoop和Hive的旅游景区数据分析

---

## 管理员API

### 一键爬取福州所有景区数据

**接口地址**：`POST /api/admin/crawl/fuzhou`

**功能说明**：
- 自动爬取福州所有热门景区的用户评论数据
- 数据包含：景区ID、名称、评分、评论内容、旅游日期、评论日期等
- 自动存储到Hadoop HDFS（JSONL格式）
- 可直接用于Hive建表分析

**请求参数**（JSON格式，可选）：
```json
{
    "target_count": 500
}
```

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| target_count | int | 目标数据量 | 500 |

**请求示例**：
```bash
curl -X POST http://localhost:5000/api/admin/crawl/fuzhou \
  -H "Content-Type: application/json" \
  -d '{"target_count": 500}'
```

**响应示例**：
```json
{
    "code": 200,
    "msg": "福州所有景区数据采集任务已启动",
    "data": {
        "task_id": 20,
        "celery_task_id": "abc-123-def",
        "scenic_spot_name": "福州（所有景区）",
        "data_source": "ctrip",
        "target_count": 500,
        "status": "running",
        "note": "数据将自动存入Hadoop HDFS",
        "create_time": "2025-12-11 02:00:00"
    }
}
```

---

## 查询任务状态

**接口地址**：`GET /api/crawler/status/{task_id}`

**请求示例**：
```bash
curl http://localhost:5000/api/crawler/status/20
```

**响应示例**：
```json
{
    "code": 200,
    "msg": "成功",
    "data": {
        "id": 20,
        "task_name": "【管理员】福州所有景区数据采集-20251211020000",
        "status": "success",
        "progress": 100,
        "actual_count": 500,
        "hdfs_path": "data/raw/20251211/ctrip_fuzhou_20_020000.jsonl",
        "create_time": "2025-12-11 02:00:00",
        "end_time": "2025-12-11 02:05:00"
    }
}
```

---

## 数据格式说明

### JSONL格式示例

每行一条JSON记录：
```json
{"review_id":"uuid-1","spot_id":"64505","spot_name":"三坊七巷","visitor_name":"张三","rating":5.0,"review_content":"很不错的景点","review_images":"[]","travel_date":"2024-10-12","review_date":"2024-10-12","helpful_count":10,"visitor_level":"高级会员","visitor_location":"福建","data_source":"ctrip","crawl_time":"2025-12-11 02:00:00"}
{"review_id":"uuid-2","spot_id":"136821","spot_name":"闽江夜游","visitor_name":"李四","rating":4.0,"review_content":"夜景很美","review_images":"[]","travel_date":"2024-11-15","review_date":"2024-11-15","helpful_count":5,"visitor_level":"普通会员","visitor_location":"江苏","data_source":"ctrip","crawl_time":"2025-12-11 02:00:00"}
```

### 字段说明

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| review_id | STRING | 评论唯一ID | "uuid-1234" |
| spot_id | STRING | 景区ID | "64505" |
| spot_name | STRING | 景区名称 | "三坊七巷" |
| visitor_name | STRING | 游客昵称 | "张三" |
| rating | DOUBLE | 评分(1-5) | 5.0 |
| review_content | STRING | 评论内容 | "很不错的景点" |
| review_images | STRING | 评论图片JSON数组 | "[]" |
| travel_date | STRING | 旅游日期 | "2024-10-12" |
| review_date | STRING | 评论日期 | "2024-10-12" |
| helpful_count | INT | 点赞数 | 10 |
| visitor_level | STRING | 游客等级 | "高级会员" |
| visitor_location | STRING | 游客所在地 | "福建" |
| data_source | STRING | 数据来源 | "ctrip" |
| crawl_time | STRING | 爬取时间 | "2025-12-11 02:00:00" |

---

## Hive建表语句

将数据导入Hive进行分析：

```sql
-- 创建外部表
CREATE EXTERNAL TABLE IF NOT EXISTS fuzhou_reviews (
    review_id STRING COMMENT '评论ID',
    spot_id STRING COMMENT '景区ID',
    spot_name STRING COMMENT '景区名称',
    visitor_name STRING COMMENT '游客昵称',
    rating DOUBLE COMMENT '评分(1-5)',
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

-- 查询示例
SELECT spot_name, COUNT(*) as review_count, AVG(rating) as avg_rating
FROM fuzhou_reviews
GROUP BY spot_name
ORDER BY review_count DESC
LIMIT 10;
```

---

## 常见Hive分析查询

### 1. 景区评论数量排行
```sql
SELECT spot_name, COUNT(*) as review_count
FROM fuzhou_reviews
GROUP BY spot_name
ORDER BY review_count DESC
LIMIT 20;
```

### 2. 月度评论趋势
```sql
SELECT SUBSTR(review_date, 1, 7) as month, COUNT(*) as count
FROM fuzhou_reviews
GROUP BY SUBSTR(review_date, 1, 7)
ORDER BY month;
```

### 3. 季节性分析
```sql
SELECT 
    CASE 
        WHEN MONTH(travel_date) IN (3,4,5) THEN '春季'
        WHEN MONTH(travel_date) IN (6,7,8) THEN '夏季'
        WHEN MONTH(travel_date) IN (9,10,11) THEN '秋季'
        ELSE '冬季'
    END as season,
    COUNT(*) as review_count,
    AVG(rating) as avg_rating
FROM fuzhou_reviews
GROUP BY CASE 
    WHEN MONTH(travel_date) IN (3,4,5) THEN '春季'
    WHEN MONTH(travel_date) IN (6,7,8) THEN '夏季'
    WHEN MONTH(travel_date) IN (9,10,11) THEN '秋季'
    ELSE '冬季'
END;
```

### 4. 高评分景区
```sql
SELECT spot_name, AVG(rating) as avg_rating, COUNT(*) as review_count
FROM fuzhou_reviews
GROUP BY spot_name
HAVING COUNT(*) >= 5
ORDER BY avg_rating DESC
LIMIT 10;
```

---

## 注意事项

1. **数据源**：目前仅实现了携程数据源
2. **爬取频率**：建议控制爬取频率，避免对目标网站造成压力
3. **数据时效**：数据包含近10年的历史评论，支持季节性分析
4. **HDFS存储**：确保Hadoop服务正常运行，默认端口9870
5. **数据格式**：JSONL格式，每行一条记录，适合Hive JsonSerDe解析
