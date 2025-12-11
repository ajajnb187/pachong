# 基于已有的hadoop-base镜像（不可修改）
FROM bde2020/hadoop-base:2.0.0-hadoop2.7.4-java8

# 定义环境变量（Hive版本、安装路径，参考Apache Hive官方文档）
ENV HIVE_VERSION=2.3.9
ENV HIVE_HOME=/opt/hive
ENV PATH=$PATH:$HIVE_HOME/bin

# 修复Debian Jessie仓库源（已归档到archive.debian.org，移除security和backports，禁用GPG）
RUN echo "deb [check-valid-until=no] http://archive.debian.org/debian jessie main" > /etc/apt/sources.list && \
    echo "Acquire::Check-Valid-Until false;" > /etc/apt/apt.conf.d/99no-check-valid-until

# 安装依赖（wget、netcat用于端口检测，MySQL驱动用于元数据连接）
RUN apt-get update && apt-get install -y --allow-unauthenticated wget netcat && \
    rm -rf /var/lib/apt/lists/*

# 下载并解压Hive2.3.9（Apache官方镜像）
RUN wget https://archive.apache.org/dist/hive/hive-$HIVE_VERSION/apache-hive-$HIVE_VERSION-bin.tar.gz && \
    tar -xzf apache-hive-$HIVE_VERSION-bin.tar.gz && \
    mv apache-hive-$HIVE_VERSION-bin $HIVE_HOME && \
    rm -f apache-hive-$HIVE_VERSION-bin.tar.gz

# 下载MySQL JDBC驱动（5.1.49，兼容Hive2.3.9和MySQL8.0，来自MySQL官方）
RUN wget https://repo1.maven.org/maven2/mysql/mysql-connector-java/5.1.49/mysql-connector-java-5.1.49.jar && \
    mv mysql-connector-java-5.1.49.jar $HIVE_HOME/lib/

# 解决Hive与Hadoop的guava版本冲突（关键：bde2020/hadoop-base的guava版本为11.0.2，Hive为14.0.1，需统一）
RUN rm /opt/hive/lib/guava-14.0.1.jar && \
    cp /opt/hadoop-2.7.4/share/hadoop/common/lib/guava-11.0.2.jar /opt/hive/lib/

# 创建Hive日志目录
RUN mkdir -p $HIVE_HOME/logs

# 暴露Hive端口（10000为HS2，9083为Metastore，参考Apache Hive官方文档）
EXPOSE 10000 9083

# 启动脚本（后续会创建，用于等待依赖服务就绪）
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]
