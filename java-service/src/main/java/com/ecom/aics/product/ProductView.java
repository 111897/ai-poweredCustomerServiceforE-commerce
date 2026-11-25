package com.ecom.aics.product;

/**
 * 商品对外投影（只包含允许展示的字段）。
 */
public record ProductView(String name,
                          String spec,
                          String price,
                          String stockStatus) {
}
