package com.tourism.tourismspringboot.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

/**
 * MyBatis Plus配置
 */
@Configuration
@MapperScan("com.tourism.tourismspringboot.mapper")
public class MyBatisPlusConfig {
    // 基础配置，分页插件可后续根据需要添加
}
