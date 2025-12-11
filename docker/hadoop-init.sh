#!/bin/bash
set -e

echo "=== Hadoop 初始化脚本开始 ==="

# 1. 更新APT源（Debian Jessie归档源）
echo "步骤1: 更新APT源..."
echo 'deb http://archive.debian.org/debian/ jessie main' > /etc/apt/sources.list
echo 'deb http://archive.debian.org/debian-security/ jessie/updates main' >> /etc/apt/sources.list

# 2. 安装SSH
if [ ! -f /usr/sbin/sshd ]; then
    echo "步骤2: 安装SSH服务..."
    apt-get update -qq
    apt-get install -y --force-yes -qq openssh-client openssh-server > /dev/null 2>&1
    echo "SSH安装完成"
else
    echo "步骤2: SSH已安装，跳过"
fi

# 3. 配置SSH免密登录
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "步骤3: 配置SSH免密登录..."
    ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa -q
    cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    echo 'StrictHostKeyChecking no' >> ~/.ssh/config
    echo "SSH配置完成"
else
    echo "步骤3: SSH密钥已存在，跳过"
fi

# 4. 启动SSH服务
echo "步骤4: 启动SSH服务..."
service ssh start

# 5. 配置JAVA_HOME
if ! grep -q "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64" /opt/hadoop-2.7.4/etc/hadoop/hadoop-env.sh; then
    echo "步骤5: 配置JAVA_HOME..."
    echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> /opt/hadoop-2.7.4/etc/hadoop/hadoop-env.sh
    echo "JAVA_HOME配置完成"
else
    echo "步骤5: JAVA_HOME已配置，跳过"
fi

# 6. 格式化HDFS（仅首次）
if [ ! -f /tmp/hadoop/.formatted ]; then
    echo "步骤6: 格式化HDFS NameNode..."
    export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
    hdfs namenode -format -force -nonInteractive
    touch /tmp/hadoop/.formatted
    echo "HDFS格式化完成"
else
    echo "步骤6: HDFS已格式化，跳过"
fi

# 7. 启动HDFS服务
echo "步骤7: 启动HDFS服务..."
/opt/hadoop-2.7.4/sbin/start-dfs.sh

# 等待HDFS启动
sleep 5

# 8. 启动YARN服务
echo "步骤8: 启动YARN服务..."
/opt/hadoop-2.7.4/sbin/start-yarn.sh

# 等待YARN启动
sleep 3

# 9. 显示运行状态
echo ""
echo "=== Hadoop 启动完成 ==="
echo "运行中的Java进程："
jps
echo ""
echo "访问信息："
echo "  - NameNode Web UI: http://localhost:50070"
echo "  - YARN ResourceManager: http://localhost:8088"
echo "  - HDFS RPC: hdfs://hadoop:9000"
echo ""
echo "=== 初始化完成，容器保持运行 ==="

# 保持容器运行
tail -f /opt/hadoop-2.7.4/logs/*.log
