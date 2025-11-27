package com.capstone.livenote.domain.user.controller;

import com.capstone.livenote.domain.user.dto.AuthResponseDto;
import com.capstone.livenote.domain.user.dto.LoginRequestDto;
import com.capstone.livenote.domain.user.dto.SignupRequestDto;
import com.capstone.livenote.domain.user.dto.UserViewDto;
import com.capstone.livenote.domain.user.entity.User;
import com.capstone.livenote.domain.user.service.UserService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;

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

    @GetMapping("/me")
    public ApiResponse<UserViewDto> me() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || auth.getPrincipal() == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "missing token");
        }
        
        Long userId = (Long) auth.getPrincipal();
        User user = userService.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "user not found"));
        
        return ApiResponse.ok(new UserViewDto(
                user.getId(),
                user.getLoginId(),
                user.getName(),
                user.getEmail(),
                user.getUiLanguage()
        ));
    }
}
