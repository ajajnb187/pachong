-- 修复MySQL数据库字符集配置
-- 使用方法: mysql -h localhost -P 23306 -u root -p < fix_charset.sql

-- 1. 修改数据库字符集
ALTER DATABASE tourism_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 修改表字符集
ALTER TABLE crawler_task CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. 查看当前字符集配置（验证）
SHOW VARIABLES LIKE 'character%';
SHOW VARIABLES LIKE 'collation%';

-- 4. 查看表结构（验证）
SHOW CREATE TABLE crawler_task;
