package com.capstone.livenote.application.ai.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "app.ai.history")
public class AiHistoryProperties {
    /**
     * 직전 N개 섹션 요약을 컨텍스트로 전송
     */
    private int previousSummaryCount = 3;

    /**
     * 직전 N개 섹션의 추천 자료를 exclude 리스트로 전송
     */
    private int previousResourceSections = 3;

    /**
     * 직전 N개 섹션의 QnA를 컨텍스트로 전송
     */
    private int previousQaSections = 3;
}
