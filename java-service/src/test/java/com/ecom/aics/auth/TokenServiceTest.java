package com.ecom.aics.auth;

import com.ecom.aics.common.ApiException;
import com.ecom.aics.config.AppProperties;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.Test;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class TokenServiceTest {

    private static final String SECRET = "unit-test-secret-32bytes-minimum-123456";

    private AppProperties props() {
        AppProperties props = new AppProperties();
        props.setAuthMode("jwt");
        props.getJwt().setSecret(SECRET);
        props.getJwt().setIssuer("aics");
        props.getJwt().setAudience("aics-client");
        props.getJwt().setTtlSeconds(300);
        return props;
    }

    @Test
    void issueAndParse() {
        TokenService service = new TokenService(props());
        String token = service.issue(1001L);
        assertEquals(1001L, service.parse("Bearer " + token).userId());
    }

    @Test
    void expiredTokenRejected() {
        AppProperties props = props();
        props.getJwt().setTtlSeconds(-1);
        TokenService service = new TokenService(props);
        String token = service.issue(1001L);
        assertThrows(ApiException.class, () -> service.parse("Bearer " + token));
    }

    @Test
    void tokenWithoutExpirationRejected() {
        SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
        String token = Jwts.builder()
                .claim("uid", 1001L)
                .setIssuer("aics")
                .setAudience("aics-client")
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
        TokenService service = new TokenService(props());
        assertThrows(ApiException.class, () -> service.parse("Bearer " + token));
    }

    @Test
    void wrongIssuerRejected() {
        AppProperties props = props();
        TokenService service = new TokenService(props);
        String token = service.issue(1001L);
        props.getJwt().setIssuer("other-issuer");
        assertThrows(ApiException.class, () -> service.parse("Bearer " + token));
    }

    @Test
    void wrongAudienceRejected() {
        AppProperties props = props();
        TokenService service = new TokenService(props);
        String token = service.issue(1001L);
        props.getJwt().setAudience("other-audience");
        assertThrows(ApiException.class, () -> service.parse("Bearer " + token));
    }

    @Test
    void missingHeaderRejected() {
        TokenService service = new TokenService(props());
        assertThrows(ApiException.class, () -> service.parse(null));
        assertThrows(ApiException.class, () -> service.parse("Basic abc"));
    }
}
