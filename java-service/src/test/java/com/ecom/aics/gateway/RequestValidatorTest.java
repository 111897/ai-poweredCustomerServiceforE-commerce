package com.ecom.aics.gateway;

import com.ecom.aics.common.ApiException;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

class RequestValidatorTest {

    @Test
    void validRequest() {
        assertDoesNotThrow(() -> RequestValidator.validate(
                new ChatRequest("sess_1001", "我买的耳机发货了吗", "order_detail")));
        assertDoesNotThrow(() -> RequestValidator.validate(
                new ChatRequest(null, "你好", null)));
    }

    @Test
    void messageRequiredAndBounded() {
        assertThrows(ApiException.class,
                () -> RequestValidator.validate(new ChatRequest(null, null, "")));
        assertThrows(ApiException.class,
                () -> RequestValidator.validate(new ChatRequest(null, "   ", "")));
        assertThrows(ApiException.class,
                () -> RequestValidator.validate(new ChatRequest(null, "x".repeat(2001), "")));
    }

    @Test
    void sessionIdMustBeSafe() {
        assertThrows(ApiException.class,
                () -> RequestValidator.validate(new ChatRequest("../etc/passwd", "你好", "")));
        assertThrows(ApiException.class,
                () -> RequestValidator.validate(new ChatRequest("会话id", "你好", "")));
        assertThrows(ApiException.class,
                () -> RequestValidator.validate(new ChatRequest("a".repeat(65), "你好", "")));
    }

    @Test
    void sceneMustBeWhitelisted() {
        assertThrows(ApiException.class,
                () -> RequestValidator.validate(new ChatRequest(null, "你好", "admin")));
        assertDoesNotThrow(() -> RequestValidator.validate(
                new ChatRequest(null, "你好", "product_detail")));
        assertDoesNotThrow(() -> RequestValidator.validate(
                new ChatRequest(null, "你好", "home")));
    }
}
