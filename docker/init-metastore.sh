#!/bin/bash
set -e

echo "等待依赖服务启动..."
sleep 10

echo "检查Hive Metastore Schema状态..."
# 设置PostgreSQL连接信息（schematool需要这些环境变量）
export HIVE_CONF_DIR=/opt/hive/conf

if /opt/hive/bin/schematool -dbType postgres -info 2>&1 | grep -q "Metastore connection URL"; then
    if /opt/hive/bin/schematool -dbType postgres -info 2>&1 | grep -q "schemaTool completed"; then
        echo "Schema已存在，跳过初始化"
    else
        echo "Schema不存在或损坏，开始初始化..."
        /opt/hive/bin/schematool -dbType postgres -initSchema || true
        echo "Schema初始化完成"
    fi
else
    echo "Schema不存在，开始初始化..."
    /opt/hive/bin/schematool -dbType postgres -initSchema || true
    echo "Schema初始化完成"
fi

echo "启动Metastore服务..."
/opt/hive/bin/hive --service metastore
