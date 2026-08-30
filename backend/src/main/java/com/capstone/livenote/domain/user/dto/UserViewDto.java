package com.capstone.livenote.domain.user.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class UserViewDto {
    private Long id;
    private String loginId;
    private String name;
    private String email;
    private String uiLanguage;
}
