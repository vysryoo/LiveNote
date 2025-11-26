package com.livenote.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class CreateLectureRequest {
    @NotBlank(message = "제목은 필수입니다")
    private String title;
    
    private String subject;
    
    @NotBlank(message = "STT 언어는 필수입니다")
    private String sttLanguage;
}

