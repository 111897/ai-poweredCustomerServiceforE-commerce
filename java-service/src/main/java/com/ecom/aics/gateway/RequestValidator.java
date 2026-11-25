package com.ecom.aics.gateway;

import com.ecom.aics.common.ApiException;
import com.ecom.aics.common.ErrorCode;

import java.util.Set;
import java.util.regex.Pattern;

/**
 * 对外对话请求参数校验（独立成类，便于单测）。
 */
public final class RequestValidator {

    private static final Pattern SESSION_ID_PATTERN =
            Pattern.compile("^[A-Za-z0-9_-]{1,64}$");
    private static final Set<String> ALLOWED_SCENES =
            Set.of("", "order_detail", "product_detail", "home");

    private RequestValidator() {
    }

    public static void validate(ChatRequest req) {
        if (req.message() == null || req.message().isBlank()
                || req.message().length() > 2000) {
            throw new ApiException(ErrorCode.E1002, "message 不能为空且不能超过 2000 字");
        }
        if (req.sessionId() != null && !req.sessionId().isBlank()
                && !SESSION_ID_PATTERN.matcher(req.sessionId()).matches()) {
            throw new ApiException(ErrorCode.E1002,
                    "sessionId 格式非法（1-64 位字母、数字、下划线或短横线）");
        }
        if (req.scene() != null && !ALLOWED_SCENES.contains(req.scene())) {
            throw new ApiException(ErrorCode.E1002, "scene 非法");
        }
    }
}
