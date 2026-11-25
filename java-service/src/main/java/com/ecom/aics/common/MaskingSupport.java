package com.ecom.aics.common;

/**
 * 脱敏工具（FR-08）：
 * 订单号、手机号、姓名、地址等敏感字段在离开 Java 前统一脱敏。
 */
public final class MaskingSupport {

    private MaskingSupport() {
    }

    /** 订单号仅显示末 4 位，如 2026112000001001 -> ****1001 */
    public static String maskOrderNo(String orderNo) {
        if (orderNo == null || orderNo.length() <= 4) {
            return "****";
        }
        return "****" + orderNo.substring(orderNo.length() - 4);
    }

    /** 手机号中间四位掩码，如 13812345678 -> 138****5678 */
    public static String maskPhone(String phone) {
        if (phone == null || phone.length() < 7) {
            return phone;
        }
        return phone.substring(0, 3) + "****" + phone.substring(phone.length() - 4);
    }

    /** 姓名首字 + *，如 张三 -> 张* */
    public static String maskName(String name) {
        if (name == null || name.isEmpty()) {
            return name;
        }
        return name.substring(0, 1) + "*";
    }

    /**
     * 地址仅保留到区/县，街道门牌隐藏。
     * 无法识别省/市/区县时返回 "**"，避免把完整地址透给模型。
     */
    public static String truncateArea(String area) {
        if (area == null || area.isBlank()) {
            return area;
        }
        String text = area.trim();
        int city = text.indexOf('市');
        int province = text.indexOf('省');
        if (city < 0 && province < 0) {
            return "**";
        }
        int anchor = Math.max(city, province);
        int start = anchor + 1;
        int best = -1;
        for (char ch : new char[]{'区', '县', '旗'}) {
            int idx = text.indexOf(ch, start);
            if (idx >= 0 && (best < 0 || idx < best)) {
                best = idx;
            }
        }
        int end = best >= 0 ? best + 1 : anchor + 1;
        return text.substring(0, Math.min(end, 20));
    }

    /** 运费状态文案 */
    public static String shipStatusText(int status) {
        return switch (status) {
            case 0 -> "未发货";
            case 1 -> "已发货";
            case 2 -> "已签收";
            default -> "未知状态";
        };
    }
}
