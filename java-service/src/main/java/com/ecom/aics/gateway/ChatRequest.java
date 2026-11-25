package com.ecom.aics.gateway;

/**
 * 唯一对外接口的请求体。
 *
 * @param sessionId 可选，首次为空由服务端生成
 * @param message   用户提问内容（1~2000 字）
 * @param scene     可选，页面来源标识（order_detail / product_detail / home）
 */
public record ChatRequest(String sessionId, String message, String scene) {
}
