-- =============================================================
-- 定向迁移：订单脱敏视图（不修改任何基表数据）
-- 执行：mysql -uroot -p --default-character-set=utf8mb4 < db/migrate_2026_11_order_views.sql
-- 说明：
--   1. 视图由 root 创建并使用 SQL SECURITY DEFINER，aics_ro 无需基表权限
--   2. v_order_ai_safe 在库内完成订单号脱敏，并保留 order_id 供明细 join
--   3. v_order_item_ai_safe 只暴露 order_id + 商品名，避免只读账号看到价格/数量
-- =============================================================

USE aics;

DROP VIEW IF EXISTS v_order_item_ai_safe;
DROP VIEW IF EXISTS v_order_ai_safe;

CREATE SQL SECURITY DEFINER VIEW v_order_ai_safe AS
SELECT
  o.id                                    AS order_id,
  CONCAT('****', RIGHT(o.order_no, 4))    AS order_no_masked,
  o.user_id,
  o.order_time,
  o.ship_status,
  o.logistics_company,
  o.logistics_location,
  o.receiver_area
FROM orders o;

CREATE SQL SECURITY DEFINER VIEW v_order_item_ai_safe AS
SELECT order_id, product_name_snapshot
FROM order_items;
