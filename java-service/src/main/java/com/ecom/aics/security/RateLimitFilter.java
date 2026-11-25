package com.ecom.aics.security;

import com.ecom.aics.auth.JwtAuthFilter;
import com.ecom.aics.config.AppProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Comparator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 简单令牌桶限流：保护公网 SSE 与 dev-token，防止刷爆 LLM 费用/线程。
 * 单机内存实现；多实例部署时应换成 Redis 令牌桶。
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 20)
public class RateLimitFilter extends OncePerRequestFilter {

    private final AppProperties props;
    private final ConcurrentHashMap<String, Bucket> buckets = new ConcurrentHashMap<>();

    public RateLimitFilter(AppProperties props) {
        this.props = props;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        if (!props.getRateLimit().isEnabled()) {
            return true;
        }
        if (!"POST".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        String uri = request.getRequestURI();
        return !(uri.equals("/api/chat/stream") || uri.equals("/api/auth/dev-token"));
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String key = resolveKey(request);
        Bucket bucket = buckets.computeIfAbsent(key, k -> new Bucket(
                props.getRateLimit().getCapacity(),
                props.getRateLimit().getRefillPerSecond()));

        if (!bucket.tryConsume()) {
            long retryAfter = Math.max(1,
                    (long) Math.ceil(1.0 / props.getRateLimit().getRefillPerSecond()));
            response.setStatus(429);
            response.setHeader("Retry-After", String.valueOf(retryAfter));
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write(
                    "{\"code\":\"E4291\",\"message\":\"请求过于频繁，请稍后再试\"}");
            return;
        }

        if (buckets.size() > props.getRateLimit().getMaxKeys()) {
            prune();
        }
        filterChain.doFilter(request, response);
    }

    private String resolveKey(HttpServletRequest request) {
        Object userId = request.getAttribute(JwtAuthFilter.ATTR_USER);
        return userId != null ? "u:" + userId : "ip:" + request.getRemoteAddr();
    }

    private void prune() {
        int max = props.getRateLimit().getMaxKeys();
        if (buckets.size() <= max) {
            return;
        }
        buckets.entrySet().stream()
                .sorted(Comparator.comparingLong(e -> e.getValue().lastUsed))
                .limit(Math.max(1, buckets.size() - max))
                .map(Map.Entry::getKey)
                .toList()
                .forEach(buckets::remove);
    }

    private static final class Bucket {
        private final int capacity;
        private final double refillPerSecond;
        private double tokens;
        private long lastRefillNanos;
        private volatile long lastUsed;

        private Bucket(int capacity, double refillPerSecond) {
            this.capacity = Math.max(1, capacity);
            this.refillPerSecond = Math.max(0.01, refillPerSecond);
            this.tokens = this.capacity;
            this.lastRefillNanos = System.nanoTime();
            this.lastUsed = System.currentTimeMillis();
        }

        private synchronized boolean tryConsume() {
            long now = System.nanoTime();
            double elapsed = (now - lastRefillNanos) / 1_000_000_000.0;
            tokens = Math.min(capacity, tokens + elapsed * refillPerSecond);
            lastRefillNanos = now;
            lastUsed = System.currentTimeMillis();
            if (tokens >= 1.0) {
                tokens -= 1.0;
                return true;
            }
            return false;
        }
    }
}
