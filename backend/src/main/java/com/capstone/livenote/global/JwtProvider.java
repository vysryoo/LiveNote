//package com.capstone.livenote.global;
//
//
//import io.jsonwebtoken.*;
//import io.jsonwebtoken.security.Keys;
//import org.springframework.beans.factory.annotation.Value;
//import org.springframework.stereotype.Component;
//
//import java.nio.charset.StandardCharsets;
//import java.security.Key;
//import java.util.Date;
//
//@Component
//public class JwtProvider {
//
//    private final Key key;
//    private final long ttlMillis;
//
//    public JwtProvider(
//            @Value("${jwt.secret}") String secret,
//            @Value("${jwt.ttl-seconds:3600}") long ttlSeconds
//    ) {
//        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
//        this.ttlMillis = ttlSeconds * 1000L;
//    }
//
//    public String generateToken(Long userId, String loginId) {
//        Date now = new Date();
//        Date exp = new Date(now.getTime() + ttlMillis);
//        return Jwts.builder()
//                .setSubject(String.valueOf(userId))   // sub = userId
//                .claim("loginId", loginId)
//                .setIssuedAt(now)
//                .setExpiration(exp)
//                .signWith(key, SignatureAlgorithm.HS256)
//                .compact();
//    }
//
//    public boolean validate(String token) {
//        try {
//            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
//            return true;
//        } catch (JwtException | IllegalArgumentException e) {
//            return false;
//        }
//    }
//
//    public Claims parseClaims(String token) {
//        return Jwts.parserBuilder().setSigningKey(key).build()
//                .parseClaimsJws(token).getBody();
//    }
//
//    public Long getUserId(String token) {
//        return Long.valueOf(parseClaims(token).getSubject());
//    }
//
//    public String getLoginId(String token) {
//        return parseClaims(token).get("loginId", String.class);
//    }
//}
