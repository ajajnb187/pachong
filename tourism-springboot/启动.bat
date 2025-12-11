@echo off
echo ========================================
echo 福州旅游景区数据分析系统 - 启动中...
echo ========================================
echo.

REM 设置环境变量
set JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF-8

echo [1/3] 检查环境...
java -version
if errorlevel 1 (
    echo 错误: 未找到Java环境，请安装JDK 1.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 编译项目...
call mvn clean package -DskipTests
if errorlevel 1 (
    echo 错误: 编译失败
    pause
    exit /b 1
)

echo.
echo [3/3] 启动应用...
echo.
echo 提示: 如果路径过长无法启动，请使用IDEA直接运行TourismSpringbootApplication.java
echo.

java -jar target\tourism-springboot-1.0.0.jar

pause
