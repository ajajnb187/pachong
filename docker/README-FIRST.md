# 一键部署指南 - 快速开始

## 🚀 部署步骤（3步完成）

### 第1步：安装Docker Desktop
确保已安装Docker Desktop并启动

### 第2步：一键部署
```bash
cd docker
.\deploy.bat
```
等待约5分钟，所有服务将自动启动

### 第3步：验证部署
部署完成后，可以访问：
- Hadoop Web UI: http://localhost:9870
- Hive JDBC: jdbc:hive2://localhost:10000

---

## ⚠️ 重要提示

### Hive表为空是正常的！
部署完成后，Hive表已创建但**没有数据**，这是正常的。

### 上传数据的步骤：

**方法1：运行爬虫服务**
```bash
cd ../tourism-flask
pip install -r requirements.txt
python app.py
```
访问 http://localhost:5000 触发爬虫，数据将自动上传到HDFS和Hive

**方法2：手动上传数据**
如果已有数据文件，可以手动上传到HDFS：
```bash
docker exec namenode hdfs dfs -put /path/to/data /tourism/data/
```

然后修复Hive分区：
```bash
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "
USE tourism_db;
MSCK REPAIR TABLE scenic_spots;
MSCK REPAIR TABLE fuzhou_reviews;
"
```

---

## 📊 启动应用服务

### Flask爬虫服务
```bash
cd tourism-flask
python app.py
# 访问 http://localhost:5000
```

### SpringBoot后端
```bash
cd tourism-springboot
mvn spring-boot:run
# 访问 http://localhost:8080
```

---

## 🔧 常见问题

### Q: 为什么Hive查询显示"表中没有数据"？
**A**: 正常！部署只创建了表结构，需要运行爬虫或手动上传数据。

### Q: 如何验证Hive是否正常？
**A**: 执行以下命令：
```bash
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "SHOW DATABASES;"
```
能看到`tourism_db`说明Hive正常。

### Q: 在新电脑上如何部署？
**A**: 
1. 复制整个项目文件夹到新电脑
2. 安装Docker Desktop
3. 进入`docker`目录，运行`deploy.bat`
4. 完成！

---

## 📚 完整文档

详细使用说明请查看：
- `一键部署指南.md` - 完整部署文档
- `使用说明.md` - 详细操作手册
- `部署成功验证报告.md` - 验证清单

---

## ✅ 部署成功标志

看到以下内容说明部署成功：
- ✅ 7个Docker容器全部运行
- ✅ Hive可以连接（`SHOW DATABASES;`成功）
- ✅ SpringBoot可以查询Hive（虽然表为空）
- ⚠️ 表中无数据是正常的，需要上传数据

---

**部署完成后，请按照上述步骤上传数据，然后即可正常使用系统！**
