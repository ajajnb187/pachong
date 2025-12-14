@echo off
chcp 65001 >nul
echo ==========================================
echo 福州旅游大数据分析系统 - 一键部署脚本
echo ==========================================
echo.

echo [1/6] 停止并清理旧环境...
docker-compose down -v 2>nul
docker volume prune -f 2>nul

echo.
echo [2/6] 拉取Docker镜像...
docker-compose pull

echo.
echo [3/6] 启动基础服务（Hadoop, PostgreSQL, Redis, MySQL）...
docker-compose up -d namenode datanode hive-metastore-postgresql redis mysql

echo.
echo [4/6] 等待基础服务启动（60秒）...
timeout /t 60 /nobreak >nul

echo.
echo [5/6] 启动Hive服务（Metastore和HiveServer2）...
docker-compose up -d hive-metastore hive-server

echo.
echo [6/6] 等待Hive服务完全启动（120秒）...
timeout /t 120 /nobreak >nul

echo.
echo [完成] 正在初始化HDFS目录...
docker exec namenode hdfs dfs -mkdir -p /tourism/data/spots
docker exec namenode hdfs dfs -mkdir -p /tourism/data/reviews
docker exec namenode hdfs dfs -chmod -R 777 /tourism

echo.
echo ==========================================
echo 验证服务状态
echo ==========================================
docker-compose ps

echo.
echo ==========================================
echo 测试Hive连接
echo ==========================================
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "SHOW DATABASES;"

echo.
echo ==========================================
echo 部署完成！
echo ==========================================
echo.
echo 服务访问地址:
echo - Hadoop NameNode Web UI: http://localhost:9870
echo - HiveServer2 JDBC: jdbc:hive2://localhost:10000
echo - Hive Metastore Thrift: thrift://localhost:9083
echo - PostgreSQL (Metastore): localhost:15432 (用户: hive/hive 数据库: metastore)
echo - Redis: localhost:6379 (密码: redis123456)
echo - MySQL (业务库): localhost:23306 (用户: tourism/tourism123 数据库: tourism_db)
echo.
echo 重要提示:
echo ✅ Hive已配置为本地执行模式（无需YARN集群）
echo ✅ 简单查询（COUNT、SELECT等）将秒级响应
echo ✅ 所有配置已优化，可直接使用
echo.
echo 常用命令:
echo - 查看服务状态: docker-compose ps
echo - 查看日志: docker-compose logs -f [服务名]
echo - 重启服务: docker-compose restart [服务名]
echo - 停止所有服务: docker-compose down
echo.
echo 详细使用说明请查看: 
echo - 一键部署指南.md (完整部署和使用说明)
echo - 使用说明.md (详细操作文档)
echo.
echo 重要提示：
echo - Hive表和VIEW视图已自动创建完成
echo - 评论表已使用正确的JsonSerDe配置
echo - 需要运行Flask爬虫上传数据到HDFS
echo - 启动Flask: cd tourism-flask, python app.py
echo - 启动SpringBoot: cd tourism-springboot, mvn spring-boot:run
echo.
echo 验证Hive环境（可选）：
echo docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW TABLES IN tourism_db"
echo docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW PARTITIONS tourism_db.scenic_spots"
echo.
pause
