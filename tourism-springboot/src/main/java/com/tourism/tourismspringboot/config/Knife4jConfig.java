package com.tourism.tourismspringboot.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;

/**
 * Knife4j接口文档配置
 */
@Configuration
public class Knife4jConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("福州旅游景区数据分析系统API文档")
                        .description("基于Hadoop和Hive的旅游景区数据分析与可视化系统")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("Tourism System")));
    }
}
