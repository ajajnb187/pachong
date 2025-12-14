@echo off
echo ==========================================
echo Fuzhou Tourism Big Data Platform - Deploy Script
echo ==========================================
echo.

echo [1/6] Stopping and cleaning old environment...
docker-compose down -v 2>nul
docker volume prune -f 2>nul

echo.
echo [2/6] Pulling Docker images...
docker-compose pull

echo.
echo [3/6] Starting base services (Hadoop, PostgreSQL, Redis, MySQL)...
docker-compose up -d namenode datanode hive-metastore-postgresql redis mysql

echo.
echo [4/6] Waiting for base services to start (60 seconds)...
timeout /t 60 /nobreak >nul

echo.
echo [5/6] Starting Hive services (Metastore and HiveServer2)...
docker-compose up -d hive-metastore hive-server

echo.
echo [6/6] Waiting for Hive services to fully start (120 seconds)...
timeout /t 120 /nobreak >nul

echo.
echo [Done] Initializing HDFS directories...
docker exec namenode hdfs dfs -mkdir -p /tourism/data/spots
docker exec namenode hdfs dfs -mkdir -p /tourism/data/reviews
docker exec namenode hdfs dfs -chmod -R 777 /tourism

echo.
echo ==========================================
echo Verifying Service Status
echo ==========================================
docker-compose ps

echo.
echo ==========================================
echo Testing Hive Connection
echo ==========================================
docker exec hive-server /opt/hive/bin/beeline -u jdbc:hive2://localhost:10000 -e "SHOW DATABASES;"

echo.
echo ==========================================
echo Deployment Complete!
echo ==========================================
echo.
echo Service Access URLs:
echo - Hadoop NameNode Web UI: http://localhost:9870
echo - HiveServer2 JDBC: jdbc:hive2://localhost:10000
echo - Hive Metastore Thrift: thrift://localhost:9083
echo - PostgreSQL (Metastore): localhost:15432 (user: hive/hive db: metastore)
echo - Redis: localhost:6379 (no password)
echo - MySQL (App DB): localhost:23306 (user: tourism/tourism123 db: tourism_db)
echo.
echo Important Notes:
echo - Hive is configured in LOCAL mode (no YARN cluster needed)
echo - Simple queries (COUNT, SELECT) will respond in seconds
echo - All configurations are optimized and ready to use
echo.
echo Common Commands:
echo - Check service status: docker-compose ps
echo - View logs: docker-compose logs -f [service-name]
echo - Restart service: docker-compose restart [service-name]
echo - Stop all services: docker-compose down
echo.
echo Next Steps:
echo - Hive tables and VIEW are automatically created
echo - Reviews table uses correct JsonSerDe configuration
echo - Run Flask crawler to upload data to HDFS
echo - Start Flask: cd tourism-flask, python app.py
echo - Start SpringBoot: cd tourism-springboot, mvn spring-boot:run
echo.
echo Verify Hive Environment (Optional):
echo docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW TABLES IN tourism_db"
echo docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "SHOW PARTITIONS tourism_db.scenic_spots"
echo.
pause
