package com.ecom.aics.api;

import com.ecom.aics.auth.TokenService;
import com.ecom.aics.common.ApiException;
import com.ecom.aics.common.ErrorCode;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 仅用于本地演示 JWT 全链路：默认关闭，且只允许回环地址。
 */
@RestController
@RequestMapping("/api/auth")
@ConditionalOnProperty(name = "aics.dev-token-enabled", havingValue = "true")
public class AuthDevController {

    public record TokenReq(Long userId) {
    }

    private final TokenService tokenService;

    public AuthDevController(TokenService tokenService) {
        this.tokenService = tokenService;
    }

    @PostMapping("/dev-token")
    public Map<String, Object> token(@RequestBody(required = false) TokenReq req,
                                     HttpServletRequest request) {
        requireLoopback(request.getRemoteAddr());
        long userId = (req == null || req.userId() == null) ? 1001L : req.userId();
        if (userId <= 0) {
            throw new ApiException(ErrorCode.E1002, "userId 必须为正数");
        }
        return Map.of(
                "token", tokenService.issue(userId),
                "tokenType", "Bearer",
                "expiresIn", tokenService.ttlSeconds(),
                "userId", userId
        );
    }

    private static void requireLoopback(String addr) {
        boolean loopback = "127.0.0.1".equals(addr)
                || "::1".equals(addr)
                || "0:0:0:0:0:0:0:1".equals(addr);
        if (!loopback) {
            throw new ApiException(ErrorCode.E1001, "dev-token 仅允许本机访问");
        }
    }
}
