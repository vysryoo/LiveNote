package com.capstone.livenote.user;

import com.capstone.livenote.global.security.JwtTokenProvider;
import jakarta.persistence.EntityNotFoundException;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder encoder;
    private final JwtTokenProvider jwtTokenProvider;

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

    @Transactional
    public Optional<User> findById(Long id) {
        return userRepository.findById(id);
    }

    @Transactional
    public UserViewDto setLanguage(Long userId, String language) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("user not found"));
        user.setUiLanguage(language != null ? language : "ko");
        userRepository.save(user);
        log.info("Language updated: userId={} lang={}", userId, user.getUiLanguage());
        return UserViewDto.from(user);
    }

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
