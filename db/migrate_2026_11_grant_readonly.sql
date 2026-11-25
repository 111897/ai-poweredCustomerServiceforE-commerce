-- =============================================================
-- 收窄 aics_ro 权限：只允许查询两个脱敏视图 + products
-- 前提：新 jar 已使用视图并验证订单查询成功（ORDER_USE_VIEW=true）
-- 注意：Docker 的 MYSQL_USER 可能创建了库级授权，必须 REVOKE ALL 后再精确授权
-- 执行：mysql -uroot -p --default-character-set=utf8mb4 < db/migrate_2026_11_grant_readonly.sql
-- =============================================================

USE aics;

CREATE USER IF NOT EXISTS 'aics_ro'@'%' IDENTIFIED BY 'aics_ro_pwd';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'aics_ro'@'%';

GRANT SELECT ON aics.v_order_ai_safe      TO 'aics_ro'@'%';
GRANT SELECT ON aics.v_order_item_ai_safe TO 'aics_ro'@'%';
GRANT SELECT ON aics.products             TO 'aics_ro'@'%';

FLUSH PRIVILEGES;
