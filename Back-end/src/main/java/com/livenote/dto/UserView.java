package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserView {
    private Long id;
    private String loginId;
    private String email;
    private String name;
    private String uiLanguage;
}

