package com.capstone.livenote.domain.user.service;

import com.capstone.livenote.domain.user.dto.AuthResponseDto;
import com.capstone.livenote.domain.user.dto.LoginRequestDto;
import com.capstone.livenote.domain.user.dto.SignupRequestDto;
import com.capstone.livenote.domain.user.dto.UserViewDto;
import com.capstone.livenote.domain.user.entity.User;
import com.capstone.livenote.domain.user.repository.UserRepository;
import jakarta.persistence.EntityNotFoundException;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    //private final JwtProvider jwt;
    private final PasswordEncoder encoder = new BCryptPasswordEncoder(); // 간단 사용

    @Transactional
    public AuthResponseDto signup(SignupRequestDto req) {
        if (userRepository.existsByLoginId(req.getLoginId())) {
            throw new IllegalArgumentException("duplicated loginId");
        }
        if (req.getEmail() != null && userRepository.existsByEmail(req.getEmail())) {
            throw new IllegalArgumentException("duplicated email");
        }

        User user = User.builder()
                .loginId(req.getLoginId())
                .password(encoder.encode(req.getPassword()))
                .name(req.getName())
                .email(req.getEmail())
                .uiLanguage("ko")
                .build();

        User saved = userRepository.save(user);

        //String token = jwt.generateToken(saved.getId(), saved.getLoginId());

        // 임시토큰
        String dummyToken = "temp-token-" + saved.getId();

//        return new AuthResponseDto(
//                token,
//                new UserViewDto(saved.getId(), saved.getLoginId(), saved.getName(), saved.getEmail(), saved.getUiLanguage())
//        );

        return new AuthResponseDto(
                dummyToken,
                new UserViewDto(
                        saved.getId(),
                        saved.getLoginId(),
                        saved.getName(),
                        saved.getEmail(),
                        saved.getUiLanguage()
                )
        );
    }

    @Transactional
    public AuthResponseDto login(LoginRequestDto req) {
        User user = userRepository.findByLoginId(req.getLoginId())
                .orElseThrow(() -> new EntityNotFoundException("no user"));

        if (!encoder.matches(req.getPassword(), user.getPassword())) {
            throw new IllegalArgumentException("bad credential");
        }

//        String token = jwt.generateToken(user.getId(), user.getLoginId());
//
//        return new AuthResponseDto(
//                token,
//                new UserViewDto(user.getId(), user.getLoginId(), user.getName(), user.getEmail(), user.getUiLanguage())
//        );
        String dummyToken = "temp-token-" + user.getId();

        return new AuthResponseDto(
                dummyToken,
                new UserViewDto(
                        user.getId(),
                        user.getLoginId(),
                        user.getName(),
                        user.getEmail(),
                        user.getUiLanguage()
                )
        );
    }
}
