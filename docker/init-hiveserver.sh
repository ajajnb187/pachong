#!/bin/bash
set -e

echo "等待Hive Metastore服务启动..."
sleep 30

echo "启动HiveServer2..."
/opt/hive/bin/hive --service hiveserver2 &

echo "等待HiveServer2启动..."
sleep 60

echo "初始化Hive基础表..."
/opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -f /opt/init-hive-tables.sh || echo "表初始化失败或已存在"

echo "创建VIEW视图和分区..."
/opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -f /opt/hive-init-partitioned.sql || echo "VIEW创建失败或已存在"

echo "HiveServer2启动完成，保持运行..."
tail -f /dev/null
