package com.ecom.aics.config;

import org.apache.catalina.connector.Connector;
import org.springframework.boot.web.embedded.tomcat.TomcatServletWebServerFactory;
import org.springframework.boot.web.server.WebServerFactoryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 为内部数据接口追加独立端口（默认 8081），避免 /internal/** 暴露在公网端口上。
 * internal-port<=0 时关闭，回退到与公网同端口。
 */
@Configuration
public class InternalPortConfig {

    private final AppProperties props;

    public InternalPortConfig(AppProperties props) {
        this.props = props;
    }

    @Bean
    public WebServerFactoryCustomizer<TomcatServletWebServerFactory> internalConnectorCustomizer() {
        return factory -> {
            int port = props.getInternalPort();
            if (port > 0) {
                Connector connector = new Connector(TomcatServletWebServerFactory.DEFAULT_PROTOCOL);
                connector.setPort(port);
                connector.setProperty("address", props.getInternalAddress());
                factory.addAdditionalTomcatConnectors(connector);
            }
        };
    }
}
