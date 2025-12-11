# Hadoop Docker容器持续重启问题解决方案

## 问题描述

在使用Docker部署Hadoop单机伪分布式集群时，容器启动后立即进入**重启循环**状态，无法正常运行Hadoop服务。

### 问题现象

1. **容器状态异常**：`docker ps`显示容器状态为`Restarting (0) X seconds ago`
2. **日志重复配置信息**：`docker logs hadoop`显示大量重复的Hadoop配置信息
3. **sed重命名错误**（早期尝试）：日志中出现`sed: cannot rename /etc/hadoop/sedXXXXXX: Device or resource busy`

### 根本原因分析

经过多次测试和排查，发现问题的根本原因是：

#### 1. **挂载配置文件导致sed命令冲突**
- 当挂载配置文件（如`core-site.xml`、`hdfs-site.xml`）到容器时
- Docker镜像的`entrypoint`脚本使用`sed -i`命令修改配置文件
- Docker挂载卷的文件系统特性阻止了`sed`的临时文件重命名操作
- 导致配置失败，容器启动异常

#### 2. **复杂的启动脚本导致超时**
- 在`command`中执行`apt-get update`、`apt-get install`等耗时操作
- 启动脚本过长且包含多个阻塞命令
- 容器启动超时后被Docker守护进程终止并重启

#### 3. **镜像兼容性问题**
- 尝试使用的`apache/hadoop:3`、`sequenceiq/hadoop-docker`等镜像
- 部分镜像已被弃用或不适合单机伪分布式部署
- 缺少必要的SSH服务或启动脚本

## 解决方案

### 最终采用方案：环境变量配置 + 手动服务启动

参考Docker Hadoop部署最佳实践，采用以下方案成功解决问题：

#### 第一步：简化docker-compose.yml配置

**关键修改点：**

1. **移除配置文件挂载**
   ```yaml
   # ❌ 错误做法 - 挂载配置文件
   volumes:
     - ./hadoop-config/core-site.xml:/opt/hadoop-2.7.4/etc/hadoop/core-site.xml
     - ./hadoop-config/hdfs-site.xml:/opt/hadoop-2.7.4/etc/hadoop/hdfs-site.xml
   
   # ✅ 正确做法 - 仅挂载数据目录
   volumes:
     - hadoop_data:/tmp/hadoop
   ```

2. **使用环境变量传递配置**
   ```yaml
   environment:
     - CORE_CONF_fs_defaultFS=hdfs://hadoop:9000
     - CORE_CONF_hadoop_tmp_dir=/tmp/hadoop
     - HDFS_CONF_dfs_namenode_name_dir=file:///tmp/hadoop/dfs/name
     - HDFS_CONF_dfs_datanode_data_dir=file:///tmp/hadoop/dfs/data
     - HDFS_CONF_dfs_replication=1
     - MAPRED_CONF_mapreduce_framework_name=yarn
     - YARN_CONF_yarn_resourcemanager_hostname=hadoop
   ```

3. **简化启动命令**
   ```yaml
   # ❌ 错误做法 - 复杂的启动脚本
   command: bash -c "apt-get update && apt-get install ... && hdfs namenode -format ..."
   
   # ✅ 正确做法 - 简单保持运行
   command: tail -f /dev/null
   ```

#### 第二步：容器启动后手动初始化Hadoop服务

容器成功运行后，执行以下初始化步骤：

```bash
# 1. 更新APT源（Debian Jessie已停止维护，需使用归档源）
docker exec hadoop bash -c "echo 'deb http://archive.debian.org/debian/ jessie main' > /etc/apt/sources.list"
docker exec hadoop bash -c "echo 'deb http://archive.debian.org/debian-security/ jessie/updates main' >> /etc/apt/sources.list"

# 2. 安装SSH服务（Hadoop需要SSH进行节点间通信）
docker exec hadoop bash -c "apt-get update"
docker exec hadoop bash -c "apt-get install -y --force-yes openssh-client openssh-server"

# 3. 配置SSH免密登录
docker exec hadoop bash -c "ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa"
docker exec hadoop bash -c "cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys"
docker exec hadoop bash -c "chmod 600 ~/.ssh/authorized_keys"
docker exec hadoop bash -c "echo 'StrictHostKeyChecking no' >> ~/.ssh/config"
docker exec hadoop bash -c "service ssh start"

# 4. 配置JAVA_HOME环境变量
docker exec hadoop bash -c "echo 'export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64' >> /opt/hadoop-2.7.4/etc/hadoop/hadoop-env.sh"

# 5. 格式化HDFS（仅首次部署需要）
docker exec hadoop bash -c "export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64 && hdfs namenode -format -force"

# 6. 启动HDFS服务
docker exec hadoop bash -c "/opt/hadoop-2.7.4/sbin/start-dfs.sh"

# 7. 启动YARN服务
docker exec hadoop bash -c "/opt/hadoop-2.7.4/sbin/start-yarn.sh"
```

#### 第三步：验证部署成功

```bash
# 检查Java进程
docker exec hadoop jps
# 输出应包含：NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager

# 测试HDFS操作
docker exec hadoop bash -c "hdfs dfs -ls /"
docker exec hadoop bash -c "hdfs dfs -mkdir -p /user/hadoop/test"
docker exec hadoop bash -c "hdfs dfs -ls /user/hadoop"
```

## 验证结果

部署成功后，应看到以下服务正常运行：

```
1244 NameNode          # HDFS名称节点
1368 DataNode          # HDFS数据节点  
1536 SecondaryNameNode # HDFS辅助名称节点
1716 ResourceManager   # YARN资源管理器
1829 NodeManager       # YARN节点管理器
```

**访问地址：**
- NameNode Web UI: `http://localhost:50070`
- YARN ResourceManager: `http://localhost:8088`
- HDFS RPC: `hdfs://hadoop:9000`

## 关键技术要点

### 1. 为什么环境变量配置有效？

`bde2020/hadoop-base`镜像的`entrypoint`脚本会：
- 读取以`CORE_CONF_`、`HDFS_CONF_`、`YARN_CONF_`等前缀的环境变量
- 自动生成对应的XML配置文件
- 避免了手动挂载配置文件导致的sed冲突

### 2. 为什么需要分步启动？

- Docker容器的健康检查有超时限制
- 在`command`中执行耗时操作（apt-get install、格式化HDFS）会导致容器启动超时
- 先让容器成功运行，再手动执行初始化操作，避免启动循环

### 3. SSH服务的作用

Hadoop伪分布式模式虽然在单节点运行，但其架构设计仍需要：
- NameNode通过SSH启动DataNode
- ResourceManager通过SSH启动NodeManager
- 因此必须安装并配置SSH免密登录

## 常见问题排查

### Q1: 容器仍然重启怎么办？

```bash
# 查看详细日志
docker logs hadoop --tail 100

# 检查是否有sed错误、JAVA_HOME错误、SSH错误等
```

### Q2: HDFS格式化失败？

确保：
- JAVA_HOME正确设置
- `/tmp/hadoop`目录有写权限
- 没有遗留的格式化标记文件

### Q3: 访问Web UI显示连接被拒绝？

检查：
- 端口映射是否正确（50070、8088）
- 防火墙是否开放对应端口
- 服务是否真正启动（使用`jps`确认）

## 参考资源

- Docker Hadoop官方镜像文档：https://github.com/big-data-europe/docker-hadoop
- Hadoop 2.7.4文档：https://hadoop.apache.org/docs/r2.7.4/
- Docker volume最佳实践：https://docs.docker.com/storage/volumes/

## 总结

Docker部署Hadoop的核心原则：
1. **避免挂载配置文件** - 使用环境变量代替
2. **简化启动命令** - 耗时操作在容器运行后执行
3. **选择合适的镜像** - 使用成熟稳定的社区镜像
4. **分步初始化** - 先运行容器，再启动服务

通过以上方案，成功解决了Hadoop Docker容器持续重启的问题，实现了稳定可靠的单机伪分布式集群部署。
