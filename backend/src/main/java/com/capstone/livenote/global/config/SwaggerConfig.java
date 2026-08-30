package com.capstone.livenote.global.config;

import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI openAPI() {
        // 1. Security 스키마 정의 (JWT 토큰 방식)
        String jwtSchemeName = "BearerAuth";
        SecurityRequirement securityRequirement = new SecurityRequirement().addList(jwtSchemeName);

        Components components = new Components()
                .addSecuritySchemes(jwtSchemeName, new SecurityScheme()
                        .name(jwtSchemeName)
                        .type(SecurityScheme.Type.HTTP) // HTTP 방식
                        .scheme("bearer")               // Bearer 토큰
                        .bearerFormat("JWT"));          // JWT 포맷

        // 2. OpenAPI 객체 생성 및 설정 주입
        return new OpenAPI()
                .info(new Info()
                        .title("LiveNote API")
                        .description("LiveNote 백엔드 API 명세서")
                        .version("1.0.0"))
                .servers(List.of(
                        new Server().url("http://54.180.135.94:8080").description("AWS EC2 Server"),
                        new Server().url("http://localhost:8080").description("Local Development")
                ))
                .addSecurityItem(securityRequirement)
                .components(components);
    }
}