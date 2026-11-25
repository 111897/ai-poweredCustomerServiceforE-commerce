package com.ecom.aics.security;

import com.ecom.aics.config.AppProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;

/**
 * 启动期安全校验：安全配置缺失时直接失败，避免默认值被误带上生产。
 */
@Component
public class SecurityStartupValidator implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(SecurityStartupValidator.class);
    private static final String LEGACY_JWT_SECRET = "dev-jwt-secret-please-change-32bytes-min";
    private static final String LEGACY_INTERNAL_TOKEN = "dev-internal-token";

    private final AppProperties props;

    public SecurityStartupValidator(AppProperties props) {
        this.props = props;
    }

    @Override
    public void run(ApplicationArguments args) {
        String token = props.getInternalToken();
        if (token == null || token.isBlank()) {
            throw new IllegalStateException(
                    "INTERNAL_TOKEN 未配置：请设置环境变量，且 Java 与 Python 必须一致");
        }

        boolean jwtMode = "jwt".equalsIgnoreCase(props.getAuthMode());
        if (jwtMode) {
            String secret = props.getJwt().getSecret();
            if (secret == null
                    || secret.getBytes(StandardCharsets.UTF_8).length < 32) {
                throw new IllegalStateException(
                        "JWT_SECRET 未配置或不足 32 字节：jwt 模式必须提供强密钥");
            }
            if (props.isStrict() && LEGACY_JWT_SECRET.equals(secret)) {
                throw new IllegalStateException("严格模式禁止使用默认 JWT_SECRET");
            }
        } else {
            log.warn("================================================================");
            log.warn(" AICS_AUTH_MODE=dev：仅允许本机回环地址，生产环境必须使用 jwt");
            log.warn("================================================================");
            if (props.isStrict()) {
                throw new IllegalStateException("严格模式禁止使用 dev 鉴权（含 dev-allow-remote）");
            }
        }

        if (props.isStrict() && LEGACY_INTERNAL_TOKEN.equals(token)) {
            throw new IllegalStateException("严格模式禁止使用默认 INTERNAL_TOKEN");
        }

        log.info("安全启动校验通过 authMode={} strict={} internalPort={}",
                props.getAuthMode(), props.isStrict(), props.getInternalPort());
    }
}
