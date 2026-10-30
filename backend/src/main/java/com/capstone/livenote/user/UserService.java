package com.capstone.livenote.user;

import com.capstone.livenote.global.security.JwtTokenProvider;
import jakarta.persistence.EntityNotFoundException;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Optional;

/**
 * 회원 가입, 로그인, 사용자 설정 변경을 맡는다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder encoder;
    private final JwtTokenProvider jwtTokenProvider;

    /**
     * 사용자를 만들고 접근 토큰을 발급한다. 비밀번호는 암호화해 저장한다.
     *
     * @param req 가입 정보. 이메일은 없을 수 있음
     * @return 접근 토큰과 사용자 정보
     * @throws IllegalArgumentException 로그인 ID나 이메일을 이미 쓰고 있는 경우
     */
    @Transactional
    public AuthResponseDto signup(SignupRequestDto req) {
        if (userRepository.existsByLoginId(req.loginId())) {
            log.warn("Signup failed: duplicated loginId={}", req.loginId());
            throw new IllegalArgumentException("duplicated loginId");
        }
        if (req.email() != null && userRepository.existsByEmail(req.email())) {
            log.warn("Signup failed: duplicated email={}", req.email());
            throw new IllegalArgumentException("duplicated email");
        }

        User user = User.builder()
                .loginId(req.loginId())
                .password(encoder.encode(req.password()))
                .name(req.name())
                .email(req.email())
                .uiLanguage("ko")
                .build();

        User saved = userRepository.save(user);
        log.info("User created: id={}", saved.getId());
        
        String token = jwtTokenProvider.createToken(saved.getId());

        return new AuthResponseDto(token, UserViewDto.from(saved));
    }

    /**
     * 로그인 ID와 비밀번호를 확인하고 접근 토큰을 발급한다.
     *
     * @param req 로그인 정보
     * @return 접근 토큰과 사용자 정보
     * @throws EntityNotFoundException 로그인 ID가 없는 경우
     * @throws IllegalArgumentException 비밀번호가 틀린 경우
     */
    @Transactional
    public AuthResponseDto login(LoginRequestDto req) {
        User user = userRepository.findByLoginId(req.loginId())
                .orElseThrow(() -> {
                    log.warn("Login failed: user not found loginId={}", req.loginId());
                    return new EntityNotFoundException("no user");
                });

        if (!encoder.matches(req.password(), user.getPassword())) {
            log.warn("Login failed: invalid password for loginId={}", req.loginId());
            throw new IllegalArgumentException("bad credential");
        }

        log.info("User logged in: id={}", user.getId());
        String token = jwtTokenProvider.createToken(user.getId());

        return new AuthResponseDto(token, UserViewDto.from(user));
    }

    /**
     * 사용자를 조회한다.
     *
     * @param id 사용자 ID
     * @return 사용자. 없으면 비어 있음
     */
    @Transactional
    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }

    /**
     * 화면 언어를 바꾼다.
     *
     * @param userId 사용자 ID
     * @param language 언어 코드. null이면 {@code ko}
     * @return 바뀐 사용자 정보
     * @throws EntityNotFoundException 사용자가 없는 경우
     */
    @Transactional
    public UserViewDto setLanguage(Long userId, String language) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("user not found"));
        user.setUiLanguage(language != null ? language : "ko");
        userRepository.save(user);
        log.info("Language updated: userId={} lang={}", userId, user.getUiLanguage());
        return UserViewDto.from(user);
    }

    /**
     * 현재 비밀번호를 확인하고 새 비밀번호로 바꾼다.
     *
     * @param userId 사용자 ID
     * @param currentPassword 현재 비밀번호
     * @param newPassword 새 비밀번호
     * @return 사용자 정보
     * @throws EntityNotFoundException 사용자가 없는 경우
     * @throws IllegalArgumentException 비밀번호가 빠졌거나 현재 비밀번호가 틀린 경우
     */
    @Transactional
    public UserViewDto changePassword(Long userId, String currentPassword, String newPassword) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("user not found"));
        if (currentPassword == null || newPassword == null) {
            throw new IllegalArgumentException("missing password");
        }
        if (!encoder.matches(currentPassword, user.getPassword())) {
            throw new IllegalArgumentException("invalid current password");
        }
        user.setPassword(encoder.encode(newPassword));
        userRepository.save(user);
        log.info("Password updated: userId={}", userId);
        return UserViewDto.from(user);
    }
}
