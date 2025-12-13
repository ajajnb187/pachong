@echo off
chcp 65001 >nul
echo ========================================
echo 修复Hive分区映射
echo ========================================
echo.
echo 说明：上传数据到HDFS后，Hive不会自动识别新分区
echo 必须执行MSCK REPAIR TABLE命令刷新分区信息
echo.

echo 正在修复scenic_spots表分区...
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "USE tourism_db; MSCK REPAIR TABLE scenic_spots;"
echo.

echo 正在修复fuzhou_reviews表分区...
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "USE tourism_db; MSCK REPAIR TABLE fuzhou_reviews;"
echo.

echo ========================================
echo 查看分区信息
echo ========================================
echo.
echo scenic_spots表分区:
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "USE tourism_db; SHOW PARTITIONS scenic_spots;"
echo.

echo fuzhou_reviews表分区:
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "USE tourism_db; SHOW PARTITIONS fuzhou_reviews;"
echo.

echo ========================================
echo 查看数据量
echo ========================================
echo.
echo scenic_spots表数据量:
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "USE tourism_db; SELECT COUNT(*) FROM scenic_spots;"
echo.

echo fuzhou_reviews表数据量:
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "USE tourism_db; SELECT COUNT(*) FROM fuzhou_reviews;"
echo.

echo ========================================
echo 修复完成！
echo ========================================
pause
