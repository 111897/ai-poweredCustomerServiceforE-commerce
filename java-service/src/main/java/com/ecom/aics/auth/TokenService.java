package com.ecom.aics.auth;

import com.ecom.aics.common.ApiException;
import com.ecom.aics.common.ErrorCode;
import com.ecom.aics.config.AppProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

/**
 * JWT 解析与签发：
 * - 解析强制校验 exp / iss / aud
 * - 仅当配置了 JWT_SECRET 时才构建密钥（dev 模式可不配置，但无法签发/校验）
 */
@Component
public class TokenService {

    private final AppProperties props;
    private final SecretKey key;

    public TokenService(AppProperties props) {
        this.props = props;
        String secret = props.getJwt().getSecret();
        if (secret == null || secret.isBlank()) {
            this.key = null;
        } else {
            if (secret.getBytes(StandardCharsets.UTF_8).length < 32) {
                throw new IllegalStateException("JWT_SECRET 至少需要 32 字节");
            }
            this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        }
    }

    /**
     * 解析 Bearer token，返回 AuthUser。
     *
     * @throws ApiException E1001 鉴权失败
     */
    public AuthUser parse(String bearer) {
        if (!"jwt".equalsIgnoreCase(props.getAuthMode())) {
            throw new IllegalStateException("dev 模式不经过 TokenService");
        }
        if (key == null) {
            throw new IllegalStateException("JWT_SECRET 未配置，无法校验 token");
        }
        if (bearer == null || !bearer.startsWith("Bearer ")) {
            throw new ApiException(ErrorCode.E1001, "缺少或无效的 Authorization");
        }
        try {
            Claims claims = Jwts.parserBuilder()
                    .setSigningKey(key)
                    .requireIssuer(props.getJwt().getIssuer())
                    .requireAudience(props.getJwt().getAudience())
                    .build()
                    .parseClaimsJws(bearer.substring(7))
                    .getBody();
            if (claims.getExpiration() == null) {
                throw new ApiException(ErrorCode.E1001, "token 缺少过期时间");
            }
            Object uid = claims.get("uid");
            if (uid == null) {
                throw new ApiException(ErrorCode.E1001, "token 中缺少 uid");
            }
            long userId = Long.parseLong(uid.toString());
            if (userId <= 0) {
                throw new ApiException(ErrorCode.E1001, "token 中 uid 非法");
            }
            return new AuthUser(userId);
        } catch (JwtException | IllegalArgumentException e) {
            throw new ApiException(ErrorCode.E1001, "token 校验失败");
        }
    }

    /**
     * 签发 token（仅供 dev-token 演示端点使用）。
     */
    public String issue(long userId) {
        if (key == null) {
            throw new IllegalStateException("JWT_SECRET 未配置，无法签发 token");
        }
        Instant now = Instant.now();
        return Jwts.builder()
                .setSubject(String.valueOf(userId))
                .claim("uid", userId)
                .setIssuer(props.getJwt().getIssuer())
                .setAudience(props.getJwt().getAudience())
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(now.plusSeconds(props.getJwt().getTtlSeconds())))
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    public long ttlSeconds() {
        return props.getJwt().getTtlSeconds();
    }
}
