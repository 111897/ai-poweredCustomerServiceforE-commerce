package com.ecom.aics.auth;

import com.ecom.aics.common.ApiException;
import com.ecom.aics.config.AppProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * 鉴权过滤器：仅保护对外接口 /api/**。
 * - jwt 模式：校验 Authorization Bearer token（exp/iss/aud）
 * - dev 模式：仅允许本机回环地址，读取 X-Debug-User-Id（缺省 1001）
 * - OPTIONS 预检与 /api/auth/dev-token 放行
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class JwtAuthFilter extends OncePerRequestFilter {

    public static final String ATTR_USER = "aics.userId";
    private static final Logger log = LoggerFactory.getLogger(JwtAuthFilter.class);

    private final TokenService tokenService;
    private final AppProperties props;

    public JwtAuthFilter(TokenService tokenService, AppProperties props) {
        this.tokenService = tokenService;
        this.props = props;
    }

    private boolean isDevMode() {
        return "dev".equalsIgnoreCase(props.getAuthMode());
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        String uri = request.getRequestURI();
        if (!uri.startsWith("/api/")) {
            return true;
        }
        // dev-token 由控制器自行做回环校验
        return uri.equals("/api/auth/dev-token");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            long userId;
            if (isDevMode()) {
                if (!props.isDevAllowRemote() && !isLoopback(request.getRemoteAddr())) {
                    writeError(response, 401, "E1001", "dev 模式仅允许本机访问");
                    return;
                }
                String debug = request.getHeader("X-Debug-User-Id");
                userId = (debug == null || debug.isBlank()) ? 1001L : Long.parseLong(debug);
                if (userId <= 0) {
                    throw new NumberFormatException();
                }
            } else {
                userId = tokenService.parse(request.getHeader("Authorization")).userId();
            }
            request.setAttribute(ATTR_USER, userId);
            filterChain.doFilter(request, response);
        } catch (ApiException e) {
            writeError(response, 401, e.getCode().name(), e.getMessage());
        } catch (NumberFormatException e) {
            writeError(response, 400, "E1002", "用户标识格式错误");
        } catch (IllegalStateException e) {
            log.error("鉴权配置异常", e);
            writeError(response, 500, "E5001", "鉴权配置异常");
        }
    }

    private static boolean isLoopback(String addr) {
        return "127.0.0.1".equals(addr)
                || "::1".equals(addr)
                || "0:0:0:0:0:0:0:1".equals(addr);
    }

    private static void writeError(HttpServletResponse response, int status,
                                   String code, String message) throws IOException {
        response.setStatus(status);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"code\":\"" + code + "\",\"message\":\"" + message + "\"}");
    }
}
