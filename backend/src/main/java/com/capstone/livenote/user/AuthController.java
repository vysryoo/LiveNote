package com.capstone.livenote.user;

import com.capstone.livenote.global.ApiResponse;
import com.capstone.livenote.global.security.JwtTokenProvider;
import com.capstone.livenote.global.security.RefreshTokenService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    // 갱신 토큰은 자바스크립트가 읽을 수 없는 쿠키로만 주고받고, 인증 API 경로에만 전송되게 함
    private static final String REFRESH_COOKIE = "livenote_refresh";
    private static final String REFRESH_COOKIE_PATH = "/api/auth";

    private final UserService userService;
    private final RefreshTokenService refreshTokenService;
    private final JwtTokenProvider jwtTokenProvider;

    @Value("${app.jwt.refresh-cookie-secure}")
    private boolean refreshCookieSecure;

    @PostMapping("/signup")
    public ResponseEntity<ApiResponse<AuthResponseDto>> signup(@RequestBody SignupRequestDto req) {
        AuthResponseDto auth = userService.signup(req);
        return withRefreshCookie(refreshTokenService.issue(auth.getUser().getId()))
                .body(ApiResponse.ok(auth));
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponseDto>> login(@RequestBody LoginRequestDto req) {
        AuthResponseDto auth = userService.login(req);
        return withRefreshCookie(refreshTokenService.issue(auth.getUser().getId()))
                .body(ApiResponse.ok(auth));
    }

    /**
     * 갱신 토큰 쿠키로 새 접근 토큰을 발급한다. 갱신 토큰도 새것으로 교체한다.
     *
     * @param refreshToken 갱신 토큰 쿠키. 없을 수 있음
     * @return 새 접근 토큰. 갱신 토큰이 없거나 만료·폐기됐으면 401과 함께 쿠키를 지움
     */
    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<AccessTokenDto>> refresh(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        return refreshTokenService.rotate(refreshToken)
                .map(rotation -> withRefreshCookie(rotation.refreshToken())
                        .body(ApiResponse.ok(new AccessTokenDto(jwtTokenProvider.createToken(rotation.userId())))))
                .orElseGet(() -> ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                        .header(HttpHeaders.SET_COOKIE, refreshCookie("", Duration.ZERO).toString())
                        .body(null));
    }

    /**
     * 갱신 토큰을 폐기하고 쿠키를 지운다. 이미 발급한 접근 토큰은 만료될 때까지 유효하다.
     *
     * @param refreshToken 갱신 토큰 쿠키. 없을 수 있음
     * @return 빈 성공 응답
     */
    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Void>> logout(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        refreshTokenService.revoke(refreshToken);
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, refreshCookie("", Duration.ZERO).toString())
                .body(ApiResponse.ok());
    }

    private ResponseEntity.BodyBuilder withRefreshCookie(String refreshToken) {
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, refreshCookie(refreshToken, refreshTokenService.validity()).toString());
    }

    private ResponseCookie refreshCookie(String value, Duration maxAge) {
        return ResponseCookie.from(REFRESH_COOKIE, value)
                .httpOnly(true)
                .secure(refreshCookieSecure)
                .sameSite("Strict")
                .path(REFRESH_COOKIE_PATH)
                .maxAge(maxAge)
                .build();
    }
}
