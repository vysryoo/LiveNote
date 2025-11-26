package com.livenote.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class SetLanguageRequest {
    @NotBlank(message = "언어는 필수입니다")
    private String language;
}

