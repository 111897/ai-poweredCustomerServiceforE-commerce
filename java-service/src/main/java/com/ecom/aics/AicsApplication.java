package com.ecom.aics;

import com.ecom.aics.config.AppProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

/**
 * AI 电商智能客服 - Java 网关与数据服务入口。
 */
@SpringBootApplication
@EnableConfigurationProperties(AppProperties.class)
public class AicsApplication {

    public static void main(String[] args) {
        SpringApplication.run(AicsApplication.class, args);
    }
}
