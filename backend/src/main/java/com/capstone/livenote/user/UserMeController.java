package com.capstone.livenote.user;

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

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserMeController {

    private final UserService userService;

    /**
     * 로그인한 사용자의 정보를 조회한다.
     *
     * @param userId 로그인한 사용자 ID
     * @return 사용자 정보. 사용자가 없으면 404
     */
    @GetMapping("/me")
    public ApiResponse<?> me(@AuthenticationPrincipal Long userId) {
        User user = userService.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "user not found"));

        return ApiResponse.ok(UserViewDto.from(user));
    }

    /**
     * 로그인한 사용자의 화면 언어를 바꾼다.
     *
     * @param userId 로그인한 사용자 ID
     * @param req 바꿀 언어. 값이 없으면 {@code ko}
     * @return 바뀐 사용자 정보. 사용자가 없으면 404
     */
    @PatchMapping("/me/language")
    public ApiResponse<UserViewDto> setLanguage(@AuthenticationPrincipal Long userId,
                                                @RequestBody SetLanguageRequest req) {
        return ApiResponse.ok(userService.setLanguage(userId, req.language()));
    }

    /**
     * 로그인한 사용자의 비밀번호를 바꾼다.
     *
     * @param userId 로그인한 사용자 ID
     * @param req 현재 비밀번호와 새 비밀번호
     * @return 사용자 정보. 비밀번호가 빠졌거나 현재 비밀번호가 틀리면 400, 사용자가 없으면 404
     */
    @PatchMapping("/me/password")
    public ApiResponse<UserViewDto> setPassword(@AuthenticationPrincipal Long userId,
                                                @RequestBody SetPasswordRequest req) {
        return ApiResponse.ok(userService.changePassword(userId, req.currentPassword(), req.newPassword()));
    }
}
