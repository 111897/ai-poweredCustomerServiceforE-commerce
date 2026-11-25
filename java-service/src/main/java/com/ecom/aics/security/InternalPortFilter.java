package com.ecom.aics.security;

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

/**
 * 内部接口端口隔离：/internal/** 只允许从内部端口访问，公网端口直接 404。
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class InternalPortFilter extends OncePerRequestFilter {

    private final AppProperties props;

    public InternalPortFilter(AppProperties props) {
        this.props = props;
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        return props.getInternalPort() <= 0
                || !request.getRequestURI().startsWith("/internal/");
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        if (request.getLocalPort() != props.getInternalPort()) {
            response.setStatus(HttpServletResponse.SC_NOT_FOUND);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"code\":\"E1001\",\"message\":\"not found\"}");
            return;
        }
        filterChain.doFilter(request, response);
    }
}
