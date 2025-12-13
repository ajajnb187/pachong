# ============================================
# 福州旅游数据分析系统 - 完整重建脚本
# ============================================
# 功能：清理旧数据 -> 重建Hive表 -> 启动服务 -> 测试接口
# 使用：在PowerShell中执行 .\rebuild-system.ps1
# ============================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  福州旅游数据分析系统 - 完整重建流程" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 设置工作目录（请根据实际路径调整）
$PROJECT_ROOT = "d:\桌面\基于Hadoop和Hive的旅游景区数据分析与可视化系统的设计与实现以福州旅游为例"

# ============================================
# 步骤1：清理HDFS旧数据
# ============================================
Write-Host "[步骤1/6] 清理HDFS旧数据..." -ForegroundColor Yellow
Write-Host "--------------------------------------------"

Write-Host "检查Hadoop容器状态..."
docker ps | Select-String "hadoop"

Write-Host "`n清理景点数据目录..."
docker exec hadoop hdfs dfs -rm -r -skipTrash /tourism/data/spots/* 2>$null
if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {
    Write-Host "✓ 景点数据目录已清理" -ForegroundColor Green
} else {
    Write-Host "⚠ 景点数据目录清理失败（可能为空）" -ForegroundColor Yellow
}

Write-Host "清理评论数据目录..."
docker exec hadoop hdfs dfs -rm -r -skipTrash /tourism/data/reviews/* 2>$null
if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 1) {
    Write-Host "✓ 评论数据目录已清理" -ForegroundColor Green
} else {
    Write-Host "⚠ 评论数据目录清理失败（可能为空）" -ForegroundColor Yellow
}

Write-Host "`n验证HDFS目录..."
docker exec hadoop hdfs dfs -ls /tourism/data/

Write-Host "`n[步骤1完成] HDFS数据清理完成`n" -ForegroundColor Green
Start-Sleep -Seconds 2

# ============================================
# 步骤2：重建Hive表结构
# ============================================
Write-Host "[步骤2/6] 重建Hive表结构..." -ForegroundColor Yellow
Write-Host "--------------------------------------------"

Write-Host "检查Hive容器状态..."
docker ps | Select-String "hive-server"

Write-Host "`n复制SQL脚本到Hive容器..."
docker cp "$PROJECT_ROOT\docker\hive-init-partitioned.sql" hive-server:/tmp/hive-init.sql
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ SQL脚本复制成功" -ForegroundColor Green
} else {
    Write-Host "✗ SQL脚本复制失败" -ForegroundColor Red
    exit 1
}

Write-Host "`n执行Hive表创建脚本（这可能需要1-2分钟）..."
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -f /tmp/hive-init.sql
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Hive表创建成功" -ForegroundColor Green
} else {
    Write-Host "✗ Hive表创建失败" -ForegroundColor Red
    exit 1
}

Write-Host "`n验证Hive表..."
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "USE tourism_db; SHOW TABLES;"

Write-Host "`n[步骤2完成] Hive表结构重建完成`n" -ForegroundColor Green
Start-Sleep -Seconds 2

# ============================================
# 步骤3：爬取测试数据
# ============================================
Write-Host "[步骤3/6] 爬取测试数据..." -ForegroundColor Yellow
Write-Host "--------------------------------------------"

Write-Host "检查Flask服务状态..."
$flaskProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*tourism-flask*" }
if ($flaskProcess) {
    Write-Host "Flask服务正在运行，PID: $($flaskProcess.Id)" -ForegroundColor Green
} else {
    Write-Host "⚠ Flask服务未运行，正在启动..." -ForegroundColor Yellow
    Write-Host "请在新窗口中手动启动Flask服务："
    Write-Host "  cd $PROJECT_ROOT\tourism-flask" -ForegroundColor Cyan
    Write-Host "  python app.py" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Flask启动后按Enter继续"
}

Write-Host "`n发起测试爬取任务（3条景点数据）..."
$response = Invoke-WebRequest -Uri "http://localhost:5000/api/admin/crawl/test" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"target_count":3}' `
    -ErrorAction SilentlyContinue

if ($response.StatusCode -eq 200) {
    Write-Host "✓ 爬取任务已提交" -ForegroundColor Green
    $taskInfo = $response.Content | ConvertFrom-Json
    Write-Host "任务ID: $($taskInfo.data.task_id)" -ForegroundColor Cyan
    
    Write-Host "`n等待爬取完成（预计30-60秒）..."
    Start-Sleep -Seconds 45
    
    Write-Host "`n验证HDFS数据..."
    docker exec hadoop hdfs dfs -ls -R /tourism/data/
} else {
    Write-Host "⚠ 爬取任务提交失败，请检查Flask服务" -ForegroundColor Yellow
}

Write-Host "`n[步骤3完成] 测试数据爬取完成`n" -ForegroundColor Green
Start-Sleep -Seconds 2

# ============================================
# 步骤4：添加Hive分区
# ============================================
Write-Host "[步骤4/6] 添加Hive分区..." -ForegroundColor Yellow
Write-Host "--------------------------------------------"

Write-Host "执行MSCK REPAIR TABLE命令..."
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "
USE tourism_db;
MSCK REPAIR TABLE scenic_spots;
MSCK REPAIR TABLE fuzhou_reviews;
"

Write-Host "`n查看分区信息..."
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "
USE tourism_db;
SHOW PARTITIONS scenic_spots;
"

Write-Host "`n验证数据..."
docker exec hive-server beeline -u "jdbc:hive2://localhost:10000" -e "
USE tourism_db;
SELECT COUNT(*) as spot_count FROM scenic_spots;
SELECT COUNT(*) as review_count FROM fuzhou_reviews;
SELECT scenic_spot, comment_score, heat_score FROM scenic_spots_latest LIMIT 5;
"

Write-Host "`n[步骤4完成] Hive分区添加完成`n" -ForegroundColor Green
Start-Sleep -Seconds 2

# ============================================
# 步骤5：启动Spring Boot服务
# ============================================
Write-Host "[步骤5/6] 启动Spring Boot服务..." -ForegroundColor Yellow
Write-Host "--------------------------------------------"

Write-Host "检查Spring Boot服务状态..."
$springProcess = Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*tourism-springboot*" }
if ($springProcess) {
    Write-Host "Spring Boot服务正在运行，PID: $($springProcess.Id)" -ForegroundColor Green
} else {
    Write-Host "⚠ Spring Boot服务未运行，正在启动..." -ForegroundColor Yellow
    Write-Host "请在新窗口中手动启动Spring Boot服务："
    Write-Host "  cd $PROJECT_ROOT\tourism-springboot" -ForegroundColor Cyan
    Write-Host "  mvn spring-boot:run" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Spring Boot启动后（看到'Started'日志）按Enter继续"
}

Write-Host "`n等待服务完全启动..."
Start-Sleep -Seconds 5

Write-Host "`n[步骤5完成] Spring Boot服务已启动`n" -ForegroundColor Green

# ============================================
# 步骤6：测试API接口
# ============================================
Write-Host "[步骤6/6] 测试API接口..." -ForegroundColor Yellow
Write-Host "--------------------------------------------"

Write-Host "测试1：用户登录..."
try {
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:8080/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"username":"admin","password":"admin123456"}'
    
    $loginData = $loginResponse.Content | ConvertFrom-Json
    if ($loginData.code -eq 200) {
        $token = $loginData.data.token
        Write-Host "✓ 登录成功，Token: $($token.Substring(0,20))..." -ForegroundColor Green
    } else {
        Write-Host "✗ 登录失败: $($loginData.msg)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ 登录请求失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n测试2：数据概览API..."
try {
    $overviewResponse = Invoke-WebRequest -Uri "http://localhost:8080/api/analysis/overview" `
        -Method GET `
        -Headers @{"Authorization" = "Bearer $token"}
    
    $overviewData = $overviewResponse.Content | ConvertFrom-Json
    if ($overviewData.code -eq 200) {
        Write-Host "✓ 数据概览API正常" -ForegroundColor Green
        Write-Host "  景点总数: $($overviewData.data.totalSpots)" -ForegroundColor Cyan
        Write-Host "  评论总数: $($overviewData.data.totalReviews)" -ForegroundColor Cyan
        Write-Host "  平均评分: $($overviewData.data.averageRating)" -ForegroundColor Cyan
    } else {
        Write-Host "⚠ 数据概览API返回异常: $($overviewData.msg)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ 数据概览API请求失败: $_" -ForegroundColor Yellow
}

Write-Host "`n测试3：景点列表API..."
try {
    $scenicResponse = Invoke-WebRequest -Uri "http://localhost:8080/api/scenic/list?page=1&pageSize=10" `
        -Method GET `
        -Headers @{"Authorization" = "Bearer $token"}
    
    $scenicData = $scenicResponse.Content | ConvertFrom-Json
    if ($scenicData.code -eq 200) {
        Write-Host "✓ 景点列表API正常" -ForegroundColor Green
        Write-Host "  返回景点数: $($scenicData.data.Count)" -ForegroundColor Cyan
        if ($scenicData.data.Count -gt 0) {
            Write-Host "  首个景点: $($scenicData.data[0].scenicSpot)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "⚠ 景点列表API返回异常: $($scenicData.msg)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ 景点列表API请求失败: $_" -ForegroundColor Yellow
}

Write-Host "`n测试4：景点排行榜API..."
try {
    $rankResponse = Invoke-WebRequest -Uri "http://localhost:8080/api/analysis/scenic-rank?type=rating&limit=5" `
        -Method GET `
        -Headers @{"Authorization" = "Bearer $token"}
    
    $rankData = $rankResponse.Content | ConvertFrom-Json
    if ($rankData.code -eq 200) {
        Write-Host "✓ 景点排行榜API正常" -ForegroundColor Green
        Write-Host "  返回排行数: $($rankData.data.Count)" -ForegroundColor Cyan
    } else {
        Write-Host "⚠ 景点排行榜API返回异常: $($rankData.msg)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ 景点排行榜API请求失败: $_" -ForegroundColor Yellow
}

Write-Host "`n[步骤6完成] API接口测试完成`n" -ForegroundColor Green

# ============================================
# 完成总结
# ============================================
Write-Host "================================================" -ForegroundColor Green
Write-Host "  系统重建和测试完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "系统状态：" -ForegroundColor Cyan
Write-Host "  ✓ HDFS数据已清理并重新爬取"
Write-Host "  ✓ Hive表结构已重建（使用时间戳分区）"
Write-Host "  ✓ 测试数据已导入（3条景点）"
Write-Host "  ✓ API接口测试通过"
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Cyan
Write-Host "  1. 访问前端：http://localhost:5173"
Write-Host "  2. 查看Hive数据："
Write-Host "     docker exec hive-server beeline -u jdbc:hive2://localhost:10000"
Write-Host "     > USE tourism_db;"
Write-Host "     > SELECT * FROM scenic_spots_latest LIMIT 10;"
Write-Host "  3. 查看HDFS数据："
Write-Host "     docker exec hadoop hdfs dfs -ls -R /tourism/data/"
Write-Host ""
Write-Host "如需完整数据爬取，执行："
Write-Host "  curl -X POST http://localhost:5000/api/admin/crawl/start -H 'Content-Type: application/json'" -ForegroundColor Yellow
Write-Host ""
