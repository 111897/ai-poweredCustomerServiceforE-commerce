package com.ecom.aics.api;

import com.ecom.aics.common.ApiException;
import com.ecom.aics.common.ErrorCode;
import com.ecom.aics.config.AppProperties;
import com.ecom.aics.order.OrderQueryService;
import com.ecom.aics.product.ProductQueryService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Map;

/**
 * 内网数据接口（仅供 Python AI 服务调用）。
 * 安全约束：
 * - 必须携带 X-Internal-Token
 * - userId 由 Python 从可信链路传入（来源于对外 token 解析）
 * - 查询结果已在 Service 内脱敏
 */
@RestController
@RequestMapping("/internal")
public class InternalController {

    public record OrderQueryReq(Long userId, Integer days, String keyword, String traceId) {
    }

    public record ProductSearchReq(String keyword, String traceId) {
    }

    private final OrderQueryService orderQueryService;
    private final ProductQueryService productQueryService;
    private final AppProperties props;

    public InternalController(OrderQueryService orderQueryService,
                              ProductQueryService productQueryService,
                              AppProperties props) {
        this.orderQueryService = orderQueryService;
        this.productQueryService = productQueryService;
        this.props = props;
    }

    private void checkToken(String token) {
        if (token == null || !MessageDigest.isEqual(
                props.getInternalToken().getBytes(StandardCharsets.UTF_8),
                token.getBytes(StandardCharsets.UTF_8))) {
            throw new ApiException(ErrorCode.E1001, "内部鉴权失败");
        }
    }

    @PostMapping("/orders/query")
    public Map<String, Object> queryOrders(
            @RequestHeader(value = "X-Internal-Token", required = false) String token,
            @RequestBody OrderQueryReq req) {
        checkToken(token);
        if (req.userId() == null) {
            throw new ApiException(ErrorCode.E1002, "userId 缺失");
        }
        return Map.of("orders",
                orderQueryService.findRecentOrders(req.userId(), req.days(), req.keyword()));
    }

    @PostMapping("/products/search")
    public Map<String, Object> searchProducts(
            @RequestHeader(value = "X-Internal-Token", required = false) String token,
            @RequestBody ProductSearchReq req) {
        checkToken(token);
        return Map.of("products", productQueryService.search(req.keyword()));
    }
}
