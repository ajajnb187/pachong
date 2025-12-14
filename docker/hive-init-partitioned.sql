-- ==========================================
-- Hive分区表设计方案
-- 基于旅游数据分析需求的最佳实践
-- ==========================================

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS tourism_db;
USE tourism_db;

-- ==========================================
-- 2. 景点信息表（按时间戳分区 - 全量覆盖策略）
-- ==========================================
-- 设计说明：
-- - 景点信息相对稳定，每次爬取为全量更新
-- - 按爬取时间戳分区，保留历史快照用于对比分析
-- - 分区格式：dt=YYYYMMDD_HHMMSS（例如：20251213_153045）
-- - 查询时默认使用最新分区视图 scenic_spots_latest
-- ==========================================

CREATE EXTERNAL TABLE IF NOT EXISTS scenic_spots (
    business_id INT COMMENT '景点业务ID',
    scenic_spot STRING COMMENT '景点名称',
    city STRING COMMENT '城市',
    zone_name STRING COMMENT '区域名称',
    comment_score DOUBLE COMMENT '评论评分',
    heat_score DOUBLE COMMENT '热度分数',
    sight_level STRING COMMENT '景点等级(如5A)',
    tag_name_list STRING COMMENT '标签列表',
    sight_category_info STRING COMMENT '景点分类信息',
    cover_image_url STRING COMMENT '封面图片URL',
    market_price STRING COMMENT '市场价格',
    is_free STRING COMMENT '是否免费',
    short_features STRING COMMENT '简短特色',
    latitude DOUBLE COMMENT '纬度',
    longitude DOUBLE COMMENT '经度',
    detail_url STRING COMMENT '详情页URL',
    crawl_time STRING COMMENT '爬取时间'
)
PARTITIONED BY (dt STRING COMMENT '爬取时间戳 YYYYMMDD_HHMMSS')
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/tourism/data/spots/'
TBLPROPERTIES ('skip.header.line.count'='0');

-- ==========================================
-- 3. 评论数据表（按时间戳分区 - 增量累积策略）
-- ==========================================
-- 设计说明：
-- - 评论数据持续增长，采用增量追加方式
-- - 按爬取时间戳分区，累积历史评论
-- - 分区格式：dt=YYYYMMDD_HHMMSS（例如：20251213_153045）
-- - 分析时可以跨分区聚合，也可以只看最新批次
-- ==========================================

CREATE EXTERNAL TABLE IF NOT EXISTS fuzhou_reviews (
    scenic_spot STRING COMMENT '景区名称',
    city STRING COMMENT '城市',
    rating DOUBLE COMMENT '评分(1-5)',
    visitor_name STRING COMMENT '游客昵称',
    review_content STRING COMMENT '评论内容',
    travel_date STRING COMMENT '旅游日期YYYY-MM-DD',
    review_date STRING COMMENT '评论日期YYYY-MM-DD',
    visitor_location STRING COMMENT '游客省份',
    ip_location STRING COMMENT 'IP属地（用于客源地统计）',
    data_source STRING COMMENT '数据来源',
    crawl_time STRING COMMENT '爬取时间'
)
PARTITIONED BY (dt STRING COMMENT '爬取时间戳 YYYYMMDD_HHMMSS')
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/tourism/data/reviews/'
TBLPROPERTIES ('skip.header.line.count'='0');

-- ==========================================
-- 4. 创建最新数据视图（简化业务层查询）
-- ==========================================

-- 景点最新数据视图（使用JOIN避免笛卡尔积）
DROP VIEW IF EXISTS scenic_spots_latest;
CREATE VIEW scenic_spots_latest AS
SELECT s.* FROM scenic_spots s
JOIN (SELECT MAX(dt) as max_dt FROM scenic_spots) t
ON s.dt = t.max_dt;

-- 评论全量数据视图（所有分区）
DROP VIEW IF EXISTS fuzhou_reviews_all;
CREATE VIEW fuzhou_reviews_all AS
SELECT * FROM fuzhou_reviews;

-- 评论最新批次视图（使用JOIN避免笛卡尔积）
DROP VIEW IF EXISTS fuzhou_reviews_latest;
CREATE VIEW fuzhou_reviews_latest AS
SELECT r.* FROM fuzhou_reviews r
JOIN (SELECT MAX(dt) as max_dt FROM fuzhou_reviews) t
ON r.dt = t.max_dt;

-- ==========================================
-- 5. 数据质量检查视图
-- ==========================================

-- 分区数据统计
DROP VIEW IF EXISTS partition_stats;
CREATE VIEW partition_stats AS
SELECT 
    'scenic_spots' as table_name,
    dt as partition_date,
    COUNT(*) as record_count,
    COUNT(DISTINCT business_id) as unique_spots
FROM scenic_spots
GROUP BY dt
UNION ALL
SELECT 
    'fuzhou_reviews' as table_name,
    dt as partition_date,
    COUNT(*) as record_count,
    COUNT(DISTINCT visitor_name) as unique_visitors
FROM fuzhou_reviews
GROUP BY dt;

-- ==========================================
-- 使用说明
-- ==========================================
-- 【重要】爬虫自动上传数据的分区格式：
--   景点：/tourism/data/spots/dt=20251213_153045/
--   评论：/tourism/data/reviews/dt=20251213_153045/
--   （时间戳格式：YYYYMMDD_HHMMSS）
--
-- 1. 每次爬取数据后，自动发现新分区：
--    MSCK REPAIR TABLE scenic_spots;
--    MSCK REPAIR TABLE fuzhou_reviews;
--
-- 2. 手动添加分区（如果MSCK失败）：
--    ALTER TABLE scenic_spots ADD IF NOT EXISTS PARTITION (dt='20251213_153045');
--    ALTER TABLE fuzhou_reviews ADD IF NOT EXISTS PARTITION (dt='20251213_153045');
--
-- 3. 查看所有分区：
--    SHOW PARTITIONS scenic_spots;
--    SHOW PARTITIONS fuzhou_reviews;
--
-- 4. 查询示例：
--    -- 查询最新景点数据（使用视图）
--    SELECT * FROM scenic_spots_latest LIMIT 10;
--    
--    -- 查询所有评论（跨所有分区）
--    SELECT * FROM fuzhou_reviews WHERE scenic_spot='三坊七巷' LIMIT 100;
--    
--    -- 查看分区数据量
--    SELECT dt, COUNT(*) as record_count 
--    FROM scenic_spots 
--    GROUP BY dt 
--    ORDER BY dt DESC;
--    
--    -- 查询特定时间段的数据（利用分区裁剪优化性能）
--    SELECT * FROM fuzhou_reviews 
--    WHERE dt >= '20251201_000000' AND dt < '20251214_000000' 
--    LIMIT 100;
--
-- 5. 分区管理：
--    -- 删除旧分区（按时间戳字符串比较）
--    ALTER TABLE fuzhou_reviews DROP IF EXISTS PARTITION (dt='20251201_120000');
--    
--    -- 批量删除旧分区（保留最近7天，需要手动列出）
--    -- 注意：时间戳格式不支持范围删除，需要逐个指定
--
-- 6. 数据验证：
--    -- 检查是否有数据
--    SELECT COUNT(*) FROM scenic_spots;
--    SELECT COUNT(*) FROM fuzhou_reviews;
--    
--    -- 查看分区统计
--    SELECT * FROM partition_stats ORDER BY partition_date DESC;
