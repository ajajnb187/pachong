package com.tourism.tourismspringboot.controller;

import java.sql.Connection;
import java.util.HashMap;
import java.util.Map;

import javax.sql.DataSource;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.tourism.tourismspringboot.common.Result;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;

/**
 * 健康检查控制器
 */
@Tag(name = "系统健康检查")
@RestController
@RequestMapping("/api/health")
public class HealthController {

    @Autowired
    @Qualifier("hiveJdbcTemplate")
    private JdbcTemplate hiveJdbcTemplate;

    @Autowired
    @Qualifier("hiveDataSource")
    private DataSource hiveDataSource;

    @Operation(summary = "健康检查")
    @GetMapping("")
    public Result<Map<String, Object>> health() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("service", "福州旅游景区数据分析系统");
        health.put("version", "1.0.0");
        return Result.success(health);
    }

    @Operation(summary = "Hive连接测试")
    @GetMapping("/hive")
    public Result<Map<String, Object>> testHive() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // 测试连接
            Connection conn = hiveDataSource.getConnection();
            result.put("hiveConnected", conn != null && !conn.isClosed());
            if (conn != null) {
                conn.close();
            }
            
            // 测试查询
            String sql = "SELECT COUNT(*) as count FROM fuzhou_reviews";
            Long count = hiveJdbcTemplate.queryForObject(sql, Long.class);
            result.put("totalReviews", count);
            result.put("status", "SUCCESS");
            result.put("message", "Hive连接正常，数据表可用");
            
        } catch (Exception e) {
            result.put("hiveConnected", false);
            result.put("status", "ERROR");
            result.put("message", "Hive连接失败：" + e.getMessage());
            result.put("error", e.getClass().getSimpleName());
        }
        
        return Result.success(result);
    }
}
