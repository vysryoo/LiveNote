package com.capstone.livenote.global.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

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
                .addSecurityItem(securityRequirement) // 모든 API에 보안 적용
                .components(components);
    }
}