package com.capstone.livenote.domain.user.controller;

import com.capstone.livenote.domain.user.dto.AuthResponseDto;
import com.capstone.livenote.domain.user.dto.LoginRequestDto;
import com.capstone.livenote.domain.user.dto.SignupRequestDto;
import com.capstone.livenote.domain.user.entity.User;
import com.capstone.livenote.domain.user.service.UserService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @PostMapping("/signup")
    public ApiResponse<AuthResponseDto> signup(@RequestBody SignupRequestDto req) {
        return ApiResponse.ok(userService.signup(req));
    }

    @PostMapping("/login")
    public ApiResponse<AuthResponseDto> login(@RequestBody LoginRequestDto req) {
        return ApiResponse.ok(userService.login(req));
    }
}

