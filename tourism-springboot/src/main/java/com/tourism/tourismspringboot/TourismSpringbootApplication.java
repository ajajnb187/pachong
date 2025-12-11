package com.tourism.tourismspringboot;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.env.Environment;

/**
 * 福州旅游景区数据分析系统启动类
 * 
 * 功能：
 * 1. 通过Hive查询福州旅游景区数据
 * 2. 提供数据分析API接口
 * 3. 支持数据可视化
 * 
 * 技术栈：
 * - Spring Boot 2.7.18
 * - MyBatis Plus 3.5.3
 * - Hive JDBC 3.1.2
 * - Knife4j 3.0.3
 */
@Slf4j
@SpringBootApplication
public class TourismSpringbootApplication {

    public static void main(String[] args) {
        ConfigurableApplicationContext context = SpringApplication.run(TourismSpringbootApplication.class, args);
        Environment env = context.getEnvironment();
        
        String port = env.getProperty("server.port");
        String contextPath = env.getProperty("server.servlet.context-path", "");
        
        log.info("\n----------------------------------------------------------\n\t" +
                "福州旅游景区数据分析系统启动成功！\n\t" +
                "应用访问地址: \t\thttp://localhost:{}{}\n\t" +
                "接口文档地址: \t\thttp://localhost:{}{}/doc.html\n\t" +
                "数据来源: \t\t\tHive (福州景区评论数据)\n" +
                "----------------------------------------------------------",
                port, contextPath, port, contextPath);
    }
}
