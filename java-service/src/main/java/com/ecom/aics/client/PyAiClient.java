package com.ecom.aics.client;

import com.ecom.aics.config.AppProperties;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * 调用 Python AI 服务的内网客户端（JDK 17 内置 HttpClient，零额外依赖）。
 * 流式读取：返回原始 SSE 字节流，由网关逐字节透传给客户端。
 */
@Component
public class PyAiClient {

    private final HttpClient client;
    private final ObjectMapper mapper;
    private final AppProperties props;

    public PyAiClient(AppProperties props, ObjectMapper mapper) {
        this.props = props;
        this.mapper = mapper;
        this.client = HttpClient.newBuilder()
                // uvicorn 不支持 h2c 明文升级，默认 HTTP/2 会导致请求体被丢弃（422），必须固定 HTTP/1.1
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofMillis(props.getPythonConnectTimeoutMs()))
                .build();
    }

    /**
     * 打开一次对话流。
     *
     * @throws Exception 连接失败或 Python 返回非 200
     */
    public InputStream openChatStream(long userId, String sessionId, String message,
                                      String scene, String traceId) throws Exception {
        Map<String, Object> body = new HashMap<>();
        body.put("userId", userId);
        body.put("sessionId", sessionId == null ? "" : sessionId);
        body.put("message", message);
        body.put("scene", scene == null ? "" : scene);
        body.put("traceId", traceId);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(props.getPythonBaseUrl() + "/internal/chat"))
                .timeout(Duration.ofMillis(props.getPythonRequestTimeoutMs()))
                .header("Content-Type", "application/json")
                .header("X-Internal-Token", props.getInternalToken())
                .header("X-Trace-Id", traceId)
                .POST(HttpRequest.BodyPublishers.ofString(
                        mapper.writeValueAsString(body), StandardCharsets.UTF_8))
                .build();

        HttpResponse<InputStream> resp = client.send(
                request, HttpResponse.BodyHandlers.ofInputStream());
        if (resp.statusCode() != 200) {
            resp.body().close();
            throw new IllegalStateException("python service status=" + resp.statusCode());
        }
        return resp.body();
    }
}
