package com.capstone.livenote.application.ai.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "app.ai.auto-cards")
public class AiAutoCardProperties {
    /**
     * 부분 요약이 도착하면 QnA 2개와 자료 2종을 자동 생성할지 여부. 평가 데이터 수집처럼 전사·요약만 필요할 때 끔
     */
    private boolean enabled = true;
}
