-- =============================================================
-- 创建 Java 服务使用的只读账号（本地学习环境）
-- 前提：已执行 db/schema.sql（全新库）或 db/migrate_2026_11_order_views.sql（已有库）
-- 目标权限：只允许查询两个脱敏视图 + products，禁止直接查询基表
-- 执行方式：用 root 账号在 Navicat 查询窗口运行，或
--   mysql -uroot -p --default-character-set=utf8mb4 < db/grant_readonly.sql
-- =============================================================

CREATE USER IF NOT EXISTS 'aics_ro'@'%' IDENTIFIED BY 'aics_ro_pwd';
ALTER USER 'aics_ro'@'%' IDENTIFIED BY 'aics_ro_pwd';

-- 先清空可能存在的库级/表级授权，再精确授予
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'aics_ro'@'%';

GRANT SELECT ON aics.v_order_ai_safe      TO 'aics_ro'@'%';
GRANT SELECT ON aics.v_order_item_ai_safe TO 'aics_ro'@'%';
GRANT SELECT ON aics.products             TO 'aics_ro'@'%';

FLUSH PRIVILEGES;
