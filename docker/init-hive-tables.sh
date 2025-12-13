CREATE DATABASE IF NOT EXISTS tourism_db;
USE tourism_db;

CREATE EXTERNAL TABLE IF NOT EXISTS scenic_spots (
    business_id INT,
    scenic_spot STRING,
    city STRING,
    zone_name STRING,
    comment_score DOUBLE,
    heat_score DOUBLE,
    sight_level STRING,
    tag_name_list STRING,
    sight_category_info STRING,
    cover_image_url STRING,
    market_price STRING,
    is_free STRING,
    short_features STRING,
    latitude DOUBLE,
    longitude DOUBLE,
    detail_url STRING,
    crawl_time STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/tourism/data/spots/';

CREATE EXTERNAL TABLE IF NOT EXISTS fuzhou_reviews (
    scenic_spot STRING,
    city STRING,
    rating DOUBLE,
    visitor_name STRING,
    review_content STRING,
    travel_date STRING,
    review_date STRING,
    data_source STRING,
    crawl_time STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/tourism/data/reviews/';
