@echo off
chcp 65001 >nul
echo ========================================
echo 福州旅游景区数据分析系统 - 一键启动
echo ========================================
echo.

REM 检查Docker是否运行
docker version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

echo [1/5] 检查Docker环境... ✓
echo.

echo [2/5] 停止旧容器（如果存在）...
docker-compose down
echo.

echo [3/5] 启动所有服务（首次启动需要下载镜像，请耐心等待）...
echo 提示: 可以打开Docker Desktop查看实时日志
echo.
docker-compose up -d
if errorlevel 1 (
    echo [错误] 启动失败
    pause
    exit /b 1
)

echo.
echo [4/5] 等待服务启动...
timeout /t 60 /nobreak >nul

echo.
echo [5/5] 初始化HDFS目录...
docker exec tourism-namenode bash /init-hdfs.sh

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo.
echo 📋 服务访问地址:
echo    - Spring Boot API:  http://localhost:8080
echo    - API文档:          http://localhost:8080/doc.html
echo    - Flask爬虫服务:    http://localhost:5000
echo    - Hadoop Web UI:    http://localhost:9870
echo    - HiveServer2 Web:  http://localhost:10002
echo.
echo 🔐 默认账号:
echo    - 管理员: admin / 123456
echo    - MySQL:  root / root123456
echo.
echo 📝 下一步操作:
echo    1. 访问 http://localhost:8080/doc.html 查看API文档
echo    2. 使用管理员账号登录
echo    3. 调用Flask爬虫接口爬取数据
echo    4. 在Hive中初始化表: docker exec -it tourism-hiveserver2 beeline -u jdbc:hive2://localhost:10000 -f /opt/hive_init.sql
echo    5. 测试数据分析接口
echo.
echo 💡 查看日志: docker-compose logs -f [服务名]
echo 💡 停止服务: docker-compose down
echo.
pause
