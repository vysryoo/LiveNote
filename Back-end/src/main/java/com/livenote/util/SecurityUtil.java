package com.livenote.util;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

public class SecurityUtil {
    public static Long getCurrentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof Long) {
            return (Long) authentication.getPrincipal();
        }
        throw new RuntimeException("인증된 사용자를 찾을 수 없습니다");
    }
    
    public static Long getCurrentUserIdOrNull() {
        try {
            return getCurrentUserId();
        } catch (RuntimeException e) {
            return null;
        }
    }
}

