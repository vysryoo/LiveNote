package com.capstone.livenote.domain.user.controller;

import com.capstone.livenote.domain.user.dto.UserViewDto;
import com.capstone.livenote.domain.user.entity.User;
import com.capstone.livenote.domain.user.service.UserService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import com.capstone.livenote.domain.user.dto.SetLanguageRequest;
import com.capstone.livenote.domain.user.dto.SetPasswordRequest;
import com.capstone.livenote.domain.user.dto.UserViewDto;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserMeController {

    private final UserService userService;

    @GetMapping("/me")
    public ApiResponse<?> me(@AuthenticationPrincipal Long userId) {
        User user = userService.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "user not found"));

        return ApiResponse.ok(UserViewDto.from(user));
    }

    @PatchMapping("/me/language")
    public ApiResponse<UserViewDto> setLanguage(@AuthenticationPrincipal Long userId,
                                                @RequestBody SetLanguageRequest req) {
        return ApiResponse.ok(userService.setLanguage(userId, req.getLanguage()));
    }

    @PatchMapping("/me/password")
    public ApiResponse<UserViewDto> setPassword(@AuthenticationPrincipal Long userId,
                                                @RequestBody SetPasswordRequest req) {
        return ApiResponse.ok(userService.changePassword(userId, req.getCurrentPassword(), req.getNewPassword()));
    }
}
