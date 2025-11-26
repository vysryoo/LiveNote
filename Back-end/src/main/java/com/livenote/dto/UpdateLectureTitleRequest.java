package com.livenote.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class UpdateLectureTitleRequest {
    @NotBlank(message = "제목은 필수입니다")
    private String title;
}

