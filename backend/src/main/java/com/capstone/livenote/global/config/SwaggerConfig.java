package com.capstone.livenote.global.config;


import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI openAPI() {
        Server devServer = new Server();
        devServer.setUrl("http://localhost:8080");          // 로컬 개발 서버
        devServer.setDescription("Local Dev Server");

        Server prodServer = new Server();
        prodServer.setUrl("http://EC2-주소:8080");           // EC2 도메인 / 퍼블릭 IP
        prodServer.setDescription("EC2 Prod Server");

        Info info = new Info()
                .title("LiveNote API")
                .version("1.0.0")
                .description("LiveNote Swagger API Description");

        return new OpenAPI()
                .info(info)
                .servers(List.of(devServer, prodServer));
    }
}