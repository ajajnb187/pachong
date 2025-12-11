#!/bin/bash
# HDFS初始化脚本 - 创建必需的目录
# 根据Flask爬虫实际存储路径创建目录

echo "==============================================="
echo "初始化HDFS目录结构..."
echo "==============================================="

# 等待HDFS启动
sleep 30

# 创建目录
# /tourism - 根目录
# /tourism/raw - Flask爬虫存储评论数据的目录
# /tourism/hive - Hive数据库目录
# /user/hive/warehouse - Hive默认warehouse目录
hdfs dfs -mkdir -p /tourism
hdfs dfs -mkdir -p /tourism/raw
hdfs dfs -mkdir -p /tourism/hive
hdfs dfs -mkdir -p /user/hive/warehouse

# 设置权限（777便于开发测试，生产环境应使用更严格的权限）
hdfs dfs -chmod -R 777 /tourism
hdfs dfs -chmod -R 777 /user/hive

echo ""
echo "HDFS目录创建完成!"
echo ""
echo "目录结构:"
hdfs dfs -ls -R /tourism
echo ""
echo "说明:"
echo "  /tourism/raw/    - Flask爬虫数据存储目录（按日期YYYYMMDD分子目录）"
echo "  /tourism/hive/   - Hive数据库目录"
echo ""
