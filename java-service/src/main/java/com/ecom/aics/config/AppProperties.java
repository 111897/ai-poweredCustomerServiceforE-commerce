package com.ecom.aics.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.ArrayList;
import java.util.List;

/**
 * 应用配置（映射 application.yml 中的 aics.* 配置项）。
 */
@ConfigurationProperties(prefix = "aics")
public class AppProperties {

    /** Python AI 服务地址（公网/内网统一入口，默认 8000） */
    private String pythonBaseUrl = "http://127.0.0.1:8000";

    /** 内部数据接口独立端口；<=0 表示关闭独立端口 */
    private int internalPort = 8081;

    /** 内部端口绑定地址；Docker 中设为 0.0.0.0 */
    private String internalAddress = "127.0.0.1";

    /** Java 与 Python 之间的共享密钥；必须显式配置，无默认值 */
    private String internalToken = "";

    /** jwt：校验 Authorization；dev：仅本地回环地址可用，读取 X-Debug-User-Id */
    private String authMode = "jwt";

    /** 严格模式：禁止 dev 鉴权、默认密钥、默认内部 token */
    private boolean strict = false;

    /** 是否允许 dev-token 端点（仅回环地址，默认关闭） */
    private boolean devTokenEnabled = false;

    /** 是否允许 dev 鉴权接受非回环来源（仅本地 Docker demo 显式开启） */
    private boolean devAllowRemote = false;

    /** Java 调 Python 的连接超时（毫秒） */
    private int pythonConnectTimeoutMs = 2000;

    /** Java 调 Python 等待响应头的超时（毫秒），不影响 SSE 流式读取 */
    private int pythonRequestTimeoutMs = 30000;

    /** 订单查询天数上限（服务端强制封顶） */
    private int orderDays = 10;

    /** 近期订单返回条数上限 */
    private int orderLimit = 20;

    /** 商品查询返回条数上限 */
    private int productLimit = 10;

    private Jwt jwt = new Jwt();
    private Cors cors = new Cors();
    private RateLimit rateLimit = new RateLimit();
    private OrderQuery orderQuery = new OrderQuery();

    public String getPythonBaseUrl() {
        return pythonBaseUrl;
    }

    public void setPythonBaseUrl(String pythonBaseUrl) {
        this.pythonBaseUrl = pythonBaseUrl;
    }

    public int getInternalPort() {
        return internalPort;
    }

    public void setInternalPort(int internalPort) {
        this.internalPort = internalPort;
    }

    public String getInternalAddress() {
        return internalAddress;
    }

    public void setInternalAddress(String internalAddress) {
        this.internalAddress = internalAddress;
    }

    public String getInternalToken() {
        return internalToken;
    }

    public void setInternalToken(String internalToken) {
        this.internalToken = internalToken;
    }

    public String getAuthMode() {
        return authMode;
    }

    public void setAuthMode(String authMode) {
        this.authMode = authMode;
    }

    public boolean isStrict() {
        return strict;
    }

    public void setStrict(boolean strict) {
        this.strict = strict;
    }

    public boolean isDevTokenEnabled() {
        return devTokenEnabled;
    }

    public void setDevTokenEnabled(boolean devTokenEnabled) {
        this.devTokenEnabled = devTokenEnabled;
    }

    public boolean isDevAllowRemote() {
        return devAllowRemote;
    }

    public void setDevAllowRemote(boolean devAllowRemote) {
        this.devAllowRemote = devAllowRemote;
    }

    public int getPythonConnectTimeoutMs() {
        return pythonConnectTimeoutMs;
    }

    public void setPythonConnectTimeoutMs(int pythonConnectTimeoutMs) {
        this.pythonConnectTimeoutMs = pythonConnectTimeoutMs;
    }

    public int getPythonRequestTimeoutMs() {
        return pythonRequestTimeoutMs;
    }

    public void setPythonRequestTimeoutMs(int pythonRequestTimeoutMs) {
        this.pythonRequestTimeoutMs = pythonRequestTimeoutMs;
    }

    public int getOrderDays() {
        return orderDays;
    }

    public void setOrderDays(int orderDays) {
        this.orderDays = orderDays;
    }

    public int getOrderLimit() {
        return orderLimit;
    }

    public void setOrderLimit(int orderLimit) {
        this.orderLimit = orderLimit;
    }

    public int getProductLimit() {
        return productLimit;
    }

    public void setProductLimit(int productLimit) {
        this.productLimit = productLimit;
    }

    public Jwt getJwt() {
        return jwt;
    }

    public void setJwt(Jwt jwt) {
        this.jwt = jwt;
    }

    public Cors getCors() {
        return cors;
    }

    public void setCors(Cors cors) {
        this.cors = cors;
    }

    public RateLimit getRateLimit() {
        return rateLimit;
    }

    public void setRateLimit(RateLimit rateLimit) {
        this.rateLimit = rateLimit;
    }

    public OrderQuery getOrderQuery() {
        return orderQuery;
    }

    public void setOrderQuery(OrderQuery orderQuery) {
        this.orderQuery = orderQuery;
    }

    public static class Jwt {
        /** HMAC 密钥；jwt 模式必须显式配置且不少于 32 字节 */
        private String secret = "";
        private String issuer = "aics";
        private String audience = "aics-client";
        private long ttlSeconds = 300;

        public String getSecret() {
            return secret;
        }

        public void setSecret(String secret) {
            this.secret = secret;
        }

        public String getIssuer() {
            return issuer;
        }

        public void setIssuer(String issuer) {
            this.issuer = issuer;
        }

        public String getAudience() {
            return audience;
        }

        public void setAudience(String audience) {
            this.audience = audience;
        }

        public long getTtlSeconds() {
            return ttlSeconds;
        }

        public void setTtlSeconds(long ttlSeconds) {
            this.ttlSeconds = ttlSeconds;
        }
    }

    public static class Cors {
        private List<String> allowedOrigins = new ArrayList<>(List.of(
                "http://127.0.0.1:5500",
                "http://localhost:5500",
                "http://localhost:3000",
                "http://localhost:5173"
        ));

        public List<String> getAllowedOrigins() {
            return allowedOrigins;
        }

        public void setAllowedOrigins(List<String> allowedOrigins) {
            this.allowedOrigins = allowedOrigins;
        }
    }

    public static class RateLimit {
        private boolean enabled = true;
        private int capacity = 30;
        private double refillPerSecond = 0.5;
        private int maxKeys = 10000;

        public boolean isEnabled() {
            return enabled;
        }

        public void setEnabled(boolean enabled) {
            this.enabled = enabled;
        }

        public int getCapacity() {
            return capacity;
        }

        public void setCapacity(int capacity) {
            this.capacity = capacity;
        }

        public double getRefillPerSecond() {
            return refillPerSecond;
        }

        public void setRefillPerSecond(double refillPerSecond) {
            this.refillPerSecond = refillPerSecond;
        }

        public int getMaxKeys() {
            return maxKeys;
        }

        public void setMaxKeys(int maxKeys) {
            this.maxKeys = maxKeys;
        }
    }

    public static class OrderQuery {
        /** true：查询脱敏视图；false：回退旧基表 SQL（回滚开关） */
        private boolean useView = true;

        public boolean isUseView() {
            return useView;
        }

        public void setUseView(boolean useView) {
            this.useView = useView;
        }
    }
}
