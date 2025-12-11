package com.tourism.tourismspringboot.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import javax.sql.DataSource;

/**
 * Hive数据源配置
 * 用于连接Hive查询福州旅游景区数据
 *
 * @author Tourism System
 */
@Configuration
public class HiveConfig {

    @Value("${hive.jdbc.url}")
    private String hiveUrl;

    @Value("${hive.jdbc.username}")
    private String username;

    @Value("${hive.jdbc.password}")
    private String password;

    @Value("${hive.jdbc.driver-class-name}")
    private String driverClassName;

    /**
     * 创建Hive数据源
     */
    @Bean(name = "hiveDataSource")
    public DataSource hiveDataSource() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource();
        dataSource.setDriverClassName(driverClassName);
        dataSource.setUrl(hiveUrl);
        dataSource.setUsername(username);
        dataSource.setPassword(password);
        return dataSource;
    }

    /**
     * 创建Hive JDBC模板
     * 用于执行Hive SQL查询
     */
    @Bean(name = "hiveJdbcTemplate")
    public JdbcTemplate hiveJdbcTemplate() {
        return new JdbcTemplate(hiveDataSource());
    }
}
