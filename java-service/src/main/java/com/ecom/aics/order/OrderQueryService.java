package com.ecom.aics.order;

import com.ecom.aics.common.MaskingSupport;
import com.ecom.aics.config.AppProperties;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 订单只读查询（FR-07 / FR-08）：
 * - 默认查询脱敏视图 v_order_ai_safe / v_order_item_ai_safe（最小权限）
 * - 可通过 aics.order-query.use-view=false 回退旧基表 SQL
 * - 强制 user_id 条件 + 时间窗口（服务端封顶）
 * - 全程参数化查询，防 SQL 注入
 * - 返回前完成脱敏投影
 */
@Service
public class OrderQueryService {

    private final JdbcTemplate jdbc;
    private final AppProperties props;

    public OrderQueryService(JdbcTemplate jdbc, AppProperties props) {
        this.jdbc = jdbc;
        this.props = props;
    }

    public List<OrderView> findRecentOrders(long userId, Integer days, String keyword) {
        int window = (days == null || days <= 0)
                ? props.getOrderDays()
                : Math.min(days, props.getOrderDays());
        String kw = (keyword == null || keyword.isBlank())
                ? null
                : "%" + keyword.trim() + "%";

        List<OrderView> rows = query(userId, window, kw);
        // 关键词是整句提问等无效条件时，回退为「用户近期订单」，避免误报“没有订单”
        if (rows.isEmpty() && kw != null) {
            rows = query(userId, window, null);
        }
        return rows;
    }

    private List<OrderView> query(long userId, int window, String kw) {
        return props.getOrderQuery().isUseView()
                ? queryView(userId, window, kw)
                : queryBase(userId, window, kw);
    }

    private List<OrderView> queryView(long userId, int window, String kw) {
        String sql = """
                SELECT o.order_no_masked,
                       GROUP_CONCAT(i.product_name_snapshot SEPARATOR '、') AS products,
                       o.ship_status,
                       o.logistics_location,
                       o.receiver_area,
                       DATE_FORMAT(o.order_time, '%Y-%m-%d %H:%i') AS order_time
                FROM v_order_ai_safe o
                LEFT JOIN v_order_item_ai_safe i ON i.order_id = o.order_id
                WHERE o.user_id = ?
                  AND o.order_time >= DATE_SUB(NOW(), INTERVAL ? DAY)
                  AND (? IS NULL OR i.product_name_snapshot LIKE ?)
                GROUP BY o.order_id, o.order_no_masked, o.ship_status,
                         o.logistics_location, o.receiver_area, o.order_time
                ORDER BY o.order_time DESC
                LIMIT ?
                """;
        return jdbc.query(sql, (rs, rowNum) -> toView(
                rs.getString("order_no_masked"),
                rs.getString("products"),
                rs.getInt("ship_status"),
                rs.getString("logistics_location"),
                rs.getString("receiver_area"),
                rs.getString("order_time")
        ), userId, window, kw, kw, props.getOrderLimit());
    }

    private List<OrderView> queryBase(long userId, int window, String kw) {
        String sql = """
                SELECT o.order_no,
                       GROUP_CONCAT(i.product_name_snapshot SEPARATOR '、') AS products,
                       o.ship_status,
                       o.logistics_location,
                       o.receiver_area,
                       DATE_FORMAT(o.order_time, '%Y-%m-%d %H:%i')        AS order_time
                FROM orders o
                LEFT JOIN order_items i ON i.order_id = o.id
                WHERE o.user_id = ?
                  AND o.order_time >= DATE_SUB(NOW(), INTERVAL ? DAY)
                  AND (? IS NULL OR i.product_name_snapshot LIKE ?)
                GROUP BY o.id
                ORDER BY o.order_time DESC
                LIMIT ?
                """;
        return jdbc.query(sql, (rs, rowNum) -> toView(
                rs.getString("order_no"),
                rs.getString("products"),
                rs.getInt("ship_status"),
                rs.getString("logistics_location"),
                rs.getString("receiver_area"),
                rs.getString("order_time")
        ), userId, window, kw, kw, props.getOrderLimit());
    }

    private static OrderView toView(String orderNo, String products, int shipStatus,
                                    String logisticsLocation, String receiverArea,
                                    String orderTime) {
        return new OrderView(
                MaskingSupport.maskOrderNo(orderNo),
                products,
                MaskingSupport.shipStatusText(shipStatus),
                logisticsLocation,
                MaskingSupport.truncateArea(receiverArea),
                orderTime
        );
    }
}
