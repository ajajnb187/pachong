-- =====================================================
-- 福州旅游景区数据分析系统 - MySQL数据库初始化脚本
-- =====================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS tourism_db 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE tourism_db;

-- =====================================================
-- 1. 用户表
-- =====================================================
CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  `username` VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码（BCrypt加密）',
  `nickname` VARCHAR(50) COMMENT '昵称',
  `email` VARCHAR(100) COMMENT '邮箱',
  `phone` VARCHAR(20) COMMENT '手机号',
  `avatar` VARCHAR(255) COMMENT '头像URL',
  `role` VARCHAR(20) DEFAULT 'admin' COMMENT '角色:admin-管理员,user-普通用户',
  `status` TINYINT DEFAULT 1 COMMENT '状态:0禁用,1启用',
  `last_login_time` DATETIME COMMENT '最后登录时间',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` TINYINT DEFAULT 0 COMMENT '删除标记:0未删除,1已删除',
  INDEX `idx_username` (`username`),
  INDEX `idx_role` (`role`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- =====================================================
-- 2. 插入默认数据
-- =====================================================

-- 插入默认管理员账户
-- 用户名：admin
-- 密码：123456（BCrypt加密后）
INSERT INTO `user` (`username`, `password`, `nickname`, `role`, `email`) 
VALUES ('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVKIUi', '系统管理员', 'admin', 'admin@tourism.com')
ON DUPLICATE KEY UPDATE `password` = VALUES(`password`);

-- =====================================================
-- 3. 爬虫任务表（与Flask共用，如果已存在则跳过）
-- =====================================================
CREATE TABLE IF NOT EXISTS `crawler_task` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
  `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
  `scenic_spot_name` VARCHAR(100) NOT NULL COMMENT '景区名称',
  `data_source` VARCHAR(50) NOT NULL COMMENT '数据来源:ctrip等',
  `target_count` INT DEFAULT 100 COMMENT '目标爬取数量',
  `actual_count` INT DEFAULT 0 COMMENT '实际爬取数量',
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '任务状态:pending,running,success,failed',
  `progress` INT DEFAULT 0 COMMENT '进度0-100',
  `start_time` DATETIME COMMENT '开始时间',
  `end_time` DATETIME COMMENT '结束时间',
  `error_msg` TEXT COMMENT '错误信息',
  `hdfs_path` VARCHAR(500) COMMENT 'HDFS存储路径',
  `create_by` BIGINT COMMENT '创建人ID',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_status` (`status`),
  INDEX `idx_data_source` (`data_source`),
  INDEX `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务表';

-- =====================================================
-- 初始化完成
-- =====================================================
SELECT '数据库初始化完成！' as message;
SELECT CONCAT('默认管理员账号: admin / 123456') as login_info;
