-- =============================================================
-- 回滚：恢复旧视图与旧授权
-- 配合 Java 侧 ORDER_USE_VIEW=false 或回退旧 jar 使用
-- 执行：mysql -uroot -p --default-character-set=utf8mb4 < db/rollback_2026_11_order_views.sql
-- =============================================================

USE aics;

DROP VIEW IF EXISTS v_order_item_ai_safe;
DROP VIEW IF EXISTS v_order_ai_safe;

CREATE SQL SECURITY DEFINER VIEW v_order_ai_safe AS
SELECT order_no, user_id, order_time, ship_status,
       logistics_company, logistics_location, receiver_area
FROM orders;

GRANT SELECT ON aics.orders      TO 'aics_ro'@'%';
GRANT SELECT ON aics.order_items TO 'aics_ro'@'%';
GRANT SELECT ON aics.products    TO 'aics_ro'@'%';

FLUSH PRIVILEGES;
