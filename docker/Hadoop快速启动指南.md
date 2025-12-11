# Hadoop 快速启动指南

## 一键启动 Hadoop 集群

### 1. 启动服务

在`docker`目录下执行：

```bash
docker-compose up -d hadoop
```

### 2. 查看启动日志

```bash
docker logs -f hadoop
```

您将看到类似以下的输出：

```
=== Hadoop 初始化脚本开始 ===
步骤1: 更新APT源...
步骤2: 安装SSH服务...
步骤3: 配置SSH免密登录...
步骤4: 启动SSH服务...
步骤5: 配置JAVA_HOME...
步骤6: 格式化HDFS NameNode...
步骤7: 启动HDFS服务...
步骤8: 启动YARN服务...

=== Hadoop 启动完成 ===
运行中的Java进程：
1244 NameNode
1368 DataNode
1536 SecondaryNameNode
1716 ResourceManager
1829 NodeManager

访问信息：
  - NameNode Web UI: http://localhost:50070
  - YARN ResourceManager: http://localhost:8088
  - HDFS RPC: hdfs://hadoop:9000
```

### 3. 验证服务状态

```bash
# 检查所有Hadoop进程
docker exec hadoop jps

# 测试HDFS操作
docker exec hadoop hdfs dfs -ls /
docker exec hadoop hdfs dfs -mkdir -p /user/hadoop/test
docker exec hadoop hdfs dfs -ls /user/hadoop
```

### 4. 访问Web界面

- **HDFS NameNode**: 打开浏览器访问 `http://localhost:50070`
- **YARN ResourceManager**: 打开浏览器访问 `http://localhost:8088`

## 常用操作命令

### HDFS操作

```bash
# 查看HDFS根目录
docker exec hadoop hdfs dfs -ls /

# 创建目录
docker exec hadoop hdfs dfs -mkdir -p /user/hadoop/data

# 上传文件到HDFS
docker exec hadoop hdfs dfs -put /本地文件路径 /hdfs目标路径

# 下载文件从HDFS
docker exec hadoop hdfs dfs -get /hdfs源路径 /本地目标路径

# 查看文件内容
docker exec hadoop hdfs dfs -cat /hdfs文件路径

# 删除文件或目录
docker exec hadoop hdfs dfs -rm -r /hdfs路径
```

### 容器管理

```bash
# 停止Hadoop容器
docker-compose stop hadoop

# 重启Hadoop容器
docker-compose restart hadoop

# 查看容器日志
docker logs hadoop

# 进入容器内部
docker exec -it hadoop bash

# 删除容器（数据会保留在volume中）
docker-compose down
```

## 故障排查

### 问题1: 容器启动失败或重启循环

**解决方法**：
```bash
# 查看完整日志
docker logs hadoop --tail 200

# 检查是否有端口冲突
netstat -an | findstr "50070 8088 9000"

# 如果端口被占用，修改docker-compose.yml中的端口映射
```

### 问题2: SSH服务未启动

**解决方法**：
```bash
# 进入容器手动启动SSH
docker exec hadoop service ssh start
```

### 问题3: HDFS格式化失败

**解决方法**：
```bash
# 删除格式化标记，重新格式化
docker exec hadoop rm -f /tmp/hadoop/.formatted
docker-compose restart hadoop
```

### 问题4: 无法访问Web UI

**检查步骤**：
1. 确认容器正在运行：`docker ps | findstr hadoop`
2. 确认端口映射正确：`docker port hadoop`
3. 检查防火墙是否阻止了端口访问
4. 确认服务已启动：`docker exec hadoop jps`

## 数据持久化

Hadoop数据存储在Docker volume中，即使删除容器，数据也不会丢失。

查看volume：
```bash
docker volume ls | findstr hadoop
```

如需完全清理（**谨慎操作，会删除所有数据**）：
```bash
docker-compose down -v
```

## 技术细节

### 配置方式
- **环境变量配置**：通过`CORE_CONF_*`、`HDFS_CONF_*`、`YARN_CONF_*`前缀的环境变量自动生成配置文件
- **避免配置文件挂载**：防止sed命令冲突导致容器重启

### 自动化流程
1. 容器启动时执行`hadoop-init.sh`脚本
2. 自动安装SSH并配置免密登录
3. 检查HDFS是否已格式化，避免重复格式化
4. 依次启动HDFS和YARN服务
5. 输出运行状态和访问信息

### 关键文件
- `docker-compose.yml`: Docker编排配置
- `hadoop-init.sh`: Hadoop自动化初始化脚本
- 详细说明文档: `Hadoop部署问题解决方案.md`

## 下一步

Hadoop集群启动成功后，可以：

1. **安装Hive**：用于SQL查询HDFS数据
2. **配置Spark**：用于大数据分析
3. **集成Flask应用**：实现数据采集和分析接口
4. **开发MapReduce程序**：进行分布式计算

---

**注意事项**：
- 首次启动需要下载镜像和安装软件，可能需要5-10分钟
- 确保Docker有足够的资源（至少4GB内存）
- 生产环境建议使用多节点集群模式
