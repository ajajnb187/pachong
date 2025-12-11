-- =============================================
-- Hive数据仓库初始化脚本
-- 用于分析存储在HDFS中的福州旅游景区数据
-- =============================================

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS tourism_db
COMMENT '福州旅游景区数据仓库'
LOCATION '/user/hive/warehouse/tourism_db.db';

USE tourism_db;

-- 2. 创建评论数据外部表（映射HDFS中的JSONL数据）
-- 字段需要与实际爬取的数据格式完全匹配
-- 表名必须为 fuzhou_reviews 以匹配 Spring Boot 代码
CREATE EXTERNAL TABLE IF NOT EXISTS fuzhou_reviews (
    scenic_spot STRING COMMENT '景区名称',
    city STRING COMMENT '城市',
    rating DOUBLE COMMENT '评分',
    visitor_name STRING COMMENT '游客名称',
    review_content STRING COMMENT '评论内容',
    travel_date STRING COMMENT '旅游日期',
    review_date STRING COMMENT '评论日期',
    data_source STRING COMMENT '数据来源',
    crawl_time STRING COMMENT '爬取时间'
)
COMMENT '景区用户评论原始数据表'
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/tourism/raw/20251211/';

-- 3. 创建景点统计汇总表
CREATE TABLE IF NOT EXISTS scenic_spots (
    spot_id STRING COMMENT '景区ID',
    spot_name STRING COMMENT '景区名称',
    city STRING COMMENT '所在城市',
    total_reviews INT COMMENT '总评论数',
    avg_rating DOUBLE COMMENT '平均评分',
    rating_5_count INT COMMENT '5星评论数',
    rating_4_count INT COMMENT '4星评论数',
    rating_3_count INT COMMENT '3星评论数',
    rating_2_count INT COMMENT '2星评论数',
    rating_1_count INT COMMENT '1星评论数',
    latest_review_date STRING COMMENT '最新评论日期',
    data_source STRING COMMENT '数据来源',
    update_time STRING COMMENT '更新时间'
)
COMMENT '景区统计汇总表'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- 4. 初始化景点统计数据
INSERT OVERWRITE TABLE scenic_spots
SELECT 
    scenic_spot AS spot_id,
    scenic_spot AS spot_name,
    city,
    COUNT(*) AS total_reviews,
    ROUND(AVG(rating), 2) AS avg_rating,
    SUM(CASE WHEN rating >= 4.5 THEN 1 ELSE 0 END) AS rating_5_count,
    SUM(CASE WHEN rating >= 3.5 AND rating < 4.5 THEN 1 ELSE 0 END) AS rating_4_count,
    SUM(CASE WHEN rating >= 2.5 AND rating < 3.5 THEN 1 ELSE 0 END) AS rating_3_count,
    SUM(CASE WHEN rating >= 1.5 AND rating < 2.5 THEN 1 ELSE 0 END) AS rating_2_count,
    SUM(CASE WHEN rating < 1.5 THEN 1 ELSE 0 END) AS rating_1_count,
    MAX(review_date) AS latest_review_date,
    data_source,
    FROM_UNIXTIME(UNIX_TIMESTAMP(), 'yyyy-MM-dd HH:mm:ss') AS update_time
FROM fuzhou_reviews
GROUP BY scenic_spot, city, data_source;
