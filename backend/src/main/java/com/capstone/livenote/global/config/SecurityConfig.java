package com.capstone.livenote.global.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.disable())
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(
                                "/api/auth/**",
                                "/api/lectures/**",

                                // WebSocket 핸드셰이크 허용
                                "/api/ws/**",

                                // 디버그용
                                "/api/dev/ws/**",
                                "/debug/**"
                        ).permitAll()
                        .anyRequest().permitAll()
                );

        return http.build();
    }
}

