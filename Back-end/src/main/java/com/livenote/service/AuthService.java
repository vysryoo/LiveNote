package com.livenote.service;

import com.livenote.dto.AuthResponse;
import com.livenote.dto.LoginRequest;
import com.livenote.dto.SignupRequest;
import com.livenote.entity.User;
import com.livenote.repository.UserRepository;
import com.livenote.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    @Transactional
    public AuthResponse signup(SignupRequest request) {
        log.info("회원가입 요청: loginId={}, email={}, name={}", request.getLoginId(), request.getEmail(), request.getName());
        
        try {
            log.debug("로그인 ID 중복 확인: {}", request.getLoginId());
            if (userRepository.existsByLoginId(request.getLoginId())) {
                log.warn("이미 존재하는 로그인 ID: {}", request.getLoginId());
                throw new RuntimeException("이미 존재하는 로그인 ID입니다");
            }
            
            log.debug("이메일 중복 확인: {}", request.getEmail());
            if (userRepository.existsByEmail(request.getEmail())) {
                log.warn("이미 존재하는 이메일: {}", request.getEmail());
                throw new RuntimeException("이미 존재하는 이메일입니다");
            }

            log.debug("사용자 생성 시작");
            User user = User.builder()
                    .loginId(request.getLoginId())
                    .password(passwordEncoder.encode(request.getPassword()))
                    .email(request.getEmail())
                    .name(request.getName())
                    .uiLanguage("한국어")
                    .build();

            user = userRepository.save(user);
            log.info("사용자 저장 완료: userId={}, loginId={}", user.getId(), user.getLoginId());
            
            String token = jwtTokenProvider.createToken(user.getId(), user.getLoginId());
            log.info("JWT 토큰 생성 완료: userId={}", user.getId());

            return AuthResponse.builder()
                    .token(token)
                    .user(AuthResponse.UserInfo.builder()
                            .id(user.getId())
                            .loginId(user.getLoginId())
                            .name(user.getName())
                            .email(user.getEmail())
                            .uiLanguage(user.getUiLanguage())
                            .build())
                    .build();
        } catch (RuntimeException e) {
            log.error("회원가입 실패: {}", e.getMessage(), e);
            throw e;
        } catch (Exception e) {
            log.error("회원가입 중 예상치 못한 오류 발생", e);
            throw new RuntimeException("회원가입 처리 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    @Transactional(readOnly = true)
    public AuthResponse login(LoginRequest request) {
        log.info("로그인 요청: loginId={}", request.getLoginId());
        
        User user = userRepository.findByLoginId(request.getLoginId())
                .orElseThrow(() -> new RuntimeException("로그인 ID 또는 비밀번호가 올바르지 않습니다"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("로그인 ID 또는 비밀번호가 올바르지 않습니다");
        }

        String token = jwtTokenProvider.createToken(user.getId(), user.getLoginId());

        return AuthResponse.builder()
                .token(token)
                .user(AuthResponse.UserInfo.builder()
                        .id(user.getId())
                        .loginId(user.getLoginId())
                        .name(user.getName())
                        .email(user.getEmail())
                        .uiLanguage(user.getUiLanguage())
                        .build())
                .build();
    }
}

