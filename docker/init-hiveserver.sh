#!/bin/bash
set -e

echo "Waiting for Hive Metastore service to start..."
sleep 30

echo "Starting HiveServer2..."
/opt/hive/bin/hive --service hiveserver2 &

echo "Waiting for HiveServer2 to start..."
sleep 60

echo "Initializing Hive tables and views..."
/opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -f /opt/hive-init-partitioned.sql || echo "Table/View initialization failed or already exists"

echo "HiveServer2 started successfully, keeping container running..."
tail -f /dev/null
