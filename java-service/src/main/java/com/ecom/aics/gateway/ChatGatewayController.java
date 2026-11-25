package com.ecom.aics.gateway;

import com.ecom.aics.auth.JwtAuthFilter;
import com.ecom.aics.client.PyAiClient;
import com.ecom.aics.common.ApiException;
import com.ecom.aics.common.ErrorCode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

/**
 * 唯一对外接口：POST /api/chat/stream
 * 校验参数 → 调用 Python /internal/chat → 逐字节透传 SSE 流。
 */
@RestController
@RequestMapping("/api/chat")
public class ChatGatewayController {

    private static final Logger log = LoggerFactory.getLogger(ChatGatewayController.class);

    private final PyAiClient pyAiClient;

    public ChatGatewayController(PyAiClient pyAiClient) {
        this.pyAiClient = pyAiClient;
    }

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public ResponseEntity<StreamingResponseBody> stream(
            @RequestBody ChatRequest req,
            @RequestAttribute(JwtAuthFilter.ATTR_USER) Long userId) {

        RequestValidator.validate(req);

        String traceId = UUID.randomUUID().toString().replace("-", "");
        StreamingResponseBody body = out -> {
            try (InputStream in = pyAiClient.openChatStream(
                    userId, req.sessionId(), req.message(), req.scene(), traceId)) {
                byte[] buf = new byte[4096];
                int n;
                while ((n = in.read(buf)) != -1) {
                    out.write(buf, 0, n);
                    out.flush();
                }
            } catch (Exception e) {
                log.warn("AI 服务调用失败 traceId={}", traceId, e);
                String err = "event: error\ndata: {\"code\":\"E2001\","
                        + "\"message\":\"AI 服务暂不可用，请稍后再试\"}\n\n";
                out.write(err.getBytes(StandardCharsets.UTF_8));
                out.flush();
            }
        };

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE,
                        MediaType.TEXT_EVENT_STREAM_VALUE + ";charset=UTF-8")
                .header(HttpHeaders.CACHE_CONTROL, "no-cache")
                .header("X-Accel-Buffering", "no")
                .body(body);
    }
}
