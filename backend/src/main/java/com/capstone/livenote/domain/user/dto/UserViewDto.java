package com.capstone.livenote.domain.user.dto;

import com.capstone.livenote.domain.user.entity.User;
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

    public static UserViewDto from(User user) {
        return new UserViewDto(
                user.getId(),
                user.getLoginId(),
                user.getName(),
                user.getEmail(),
                user.getUiLanguage()
        );
    }
}
