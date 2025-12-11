@echo off
chcp 65001
echo ============================================
echo   Hive数据库初始化脚本
echo   功能：创建tourism_db数据库和表结构
echo ============================================
echo.

echo [1/3] 检查Hive Server运行状态...
docker ps --filter name=hive-server --format "{{.Status}}" | findstr "Up" >nul
if errorlevel 1 (
    echo [错误] Hive Server未运行，请先启动: docker-compose up -d hive-server
    pause
    exit /b 1
)
echo [✓] Hive Server正在运行

echo.
echo [2/3] 复制SQL脚本到Hive容器...
docker cp src\main\resources\init-hive.sql hive-server:/tmp/init-hive.sql
if errorlevel 1 (
    echo [错误] 复制SQL脚本失败
    pause
    exit /b 1
)
echo [✓] SQL脚本已复制

echo.
echo [3/3] 执行Hive建表脚本（这可能需要1-2分钟）...
docker exec hive-server bash -c "hive -f /tmp/init-hive.sql"

echo.
echo ============================================
echo   初始化完成！
echo   - 数据库：tourism_db
echo   - 外部表：fuzhou_scenic_reviews
echo   - 统计表：scenic_review_stats
echo ============================================
pause
