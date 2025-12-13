package com.tourism.tourismspringboot.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;

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
                        .description("基于Hadoop和Hive的旅游景区数据分析与可视化系统\n\n" +
                                "使用说明：\n" +
                                "1. 调用 /api/auth/login 接口获取token\n" +
                                "2. 点击右上角【Authorize】按钮，输入token值\n" +
                                "3. 之后所有接口调用将自动携带token")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("Tourism System")))
                .components(new Components()
                        .addSecuritySchemes("satoken", new SecurityScheme()
                                .type(SecurityScheme.Type.APIKEY)
                                .in(SecurityScheme.In.HEADER)
                                .name("satoken")
                                .description("SaToken认证，输入登录接口返回的token值")))
                .addSecurityItem(new SecurityRequirement().addList("satoken"));
    }
}
