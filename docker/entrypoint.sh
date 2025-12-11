#!/bin/bash
set -e

# 函数：等待端口就绪（参考Docker官方最佳实践）
wait_for_port() {
    local host=$1
    local port=$2
    until nc -z $host $port; do
        echo "Waiting for $host:$port to be ready..."
        sleep 5
    done
}

# 等待Hadoop NameNode（50070）和MySQL（3306）就绪
wait_for_port hadoop 50070
wait_for_port mysql 3306

# 初始化Hive元数据库（仅第一次启动时执行）
if [ ! -f /opt/hive/metastore_initialized ]; then
    echo "Initializing Hive Metastore..."
    schematool -initSchema -dbType mysql -verbose
    touch /opt/hive/metastore_initialized
fi

# 启动Hive Metastore和HiveServer2（后台运行，参考Apache Hive官方启动方式）
echo "Starting Hive Metastore..."
nohup hive --service metastore > $HIVE_HOME/logs/metastore.log 2>&1 &
wait_for_port localhost 9083

echo "Starting HiveServer2..."
nohup hive --service hiveserver2 > $HIVE_HOME/logs/hiveserver2.log 2>&1 &

# 保持容器运行（Docker最佳实践）
tail -f $HIVE_HOME/logs/hiveserver2.log
