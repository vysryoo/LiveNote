package com.capstone.livenote.user;

/**
 * 갱신 토큰으로 새로 발급한 접근 토큰.
 *
 * @param token 접근 토큰(JWT)
 */
public record AccessTokenDto(String token) {
}
