package com.capstone.livenote.user;

public record UserViewDto(Long id, String loginId, String name, String email, String uiLanguage) {

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
