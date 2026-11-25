package com.ecom.aics.order;

/**
 * 订单对外投影（已脱敏，仅包含允许反馈的字段）。
 *
 * @param orderNoMasked     订单号（末 4 位）
 * @param productName       商品名称
 * @param shipStatus        发货状态文案
 * @param logisticsLocation 物流当前位置
 * @param receiverArea      收货区县
 * @param orderTime         下单时间（yyyy-MM-dd HH:mm）
 */
public record OrderView(String orderNoMasked,
                        String productName,
                        String shipStatus,
                        String logisticsLocation,
                        String receiverArea,
                        String orderTime) {
}
