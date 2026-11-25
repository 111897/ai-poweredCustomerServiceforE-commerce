package com.ecom.aics.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

/**
 * Web 配置：CORS 使用显式白名单；dev 模式才允许 X-Debug-User-Id。
 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final AppProperties props;

    public WebConfig(AppProperties props) {
        this.props = props;
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        List<String> origins = props.getCors().getAllowedOrigins();
        String[] headers = "dev".equalsIgnoreCase(props.getAuthMode())
                ? new String[]{"Authorization", "Content-Type", "X-Debug-User-Id"}
                : new String[]{"Authorization", "Content-Type"};

        registry.addMapping("/api/**")
                .allowedOrigins(origins.toArray(new String[0]))
                .allowedMethods("POST", "OPTIONS")
                .allowedHeaders(headers)
                .maxAge(3600);
    }
}
