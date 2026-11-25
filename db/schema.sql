-- =============================================================
-- 电商 AI 智能客服 示例库结构（MySQL 8）
-- ⚠️ 本文件含 DROP TABLE，仅用于全新数据库；已有数据的库请使用
--    db/migrate_2026_11_*.sql 定向迁移，切勿直接执行本文件。
-- 说明：字段为设计草案，接入真实电商库时请按实际字段做映射，
--       并为本模块创建仅 SELECT 权限的只读账号（见文件末尾说明）。
-- =============================================================

CREATE DATABASE IF NOT EXISTS aics DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aics;

-- ---------------------------
-- 商品表
-- ---------------------------
DROP VIEW IF EXISTS v_order_item_ai_safe;
DROP VIEW IF EXISTS v_order_ai_safe;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
  id            BIGINT        NOT NULL AUTO_INCREMENT,
  name          VARCHAR(100)  NOT NULL COMMENT '商品名称',
  category      VARCHAR(32)   NOT NULL COMMENT '类目',
  spec          VARCHAR(64)            COMMENT '规格',
  price         DECIMAL(10,2) NOT NULL COMMENT '价格',
  stock         INT           NOT NULL DEFAULT 0 COMMENT '库存数量',
  stock_status  TINYINT       NOT NULL DEFAULT 1 COMMENT '1有货 0缺货',
  description   TEXT                   COMMENT '描述',
  PRIMARY KEY (id),
  KEY idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品表';

-- ---------------------------
-- 订单表
-- ---------------------------
CREATE TABLE orders (
  id                 BIGINT       NOT NULL AUTO_INCREMENT,
  order_no           VARCHAR(32)  NOT NULL COMMENT '订单号（不对外明文）',
  user_id            BIGINT       NOT NULL COMMENT '下单用户',
  order_time         DATETIME     NOT NULL COMMENT '下单时间',
  pay_status         TINYINT      NOT NULL DEFAULT 1 COMMENT '0未付 1已付',
  ship_status        TINYINT      NOT NULL DEFAULT 0 COMMENT '0未发货 1已发货 2已签收',
  logistics_company  VARCHAR(32)           COMMENT '物流公司',
  logistics_no       VARCHAR(32)           COMMENT '物流单号（不对外）',
  logistics_location VARCHAR(128)          COMMENT '物流当前位置',
  receiver_name      VARCHAR(32)           COMMENT '收件人（掩码）',
  receiver_area      VARCHAR(64)           COMMENT '收货区县（仅到区县）',
  PRIMARY KEY (id),
  UNIQUE KEY uk_order_no (order_no),
  KEY idx_user_time (user_id, order_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- ---------------------------
-- 订单明细表
-- ---------------------------
CREATE TABLE order_items (
  id                    BIGINT       NOT NULL AUTO_INCREMENT,
  order_id              BIGINT       NOT NULL,
  product_id            BIGINT       NOT NULL,
  product_name_snapshot VARCHAR(100) NOT NULL COMMENT '下单时商品名',
  spec                  VARCHAR(64),
  num                   INT          NOT NULL DEFAULT 1,
  price                 DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_order (order_id),
  KEY idx_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细表';

-- ---------------------------
-- AI 安全视图（库内脱敏 + 最小列）
-- ---------------------------
CREATE SQL SECURITY DEFINER VIEW v_order_ai_safe AS
SELECT
  o.id                                 AS order_id,
  CONCAT('****', RIGHT(o.order_no, 4)) AS order_no_masked,
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

-- ---------------------------
-- 示例数据（user_id: 1001 / 1002）
-- ---------------------------
INSERT INTO products (name, category, spec, price, stock, stock_status, description) VALUES
('降噪蓝牙耳机', '数码', '黑色 / 蓝牙5.3 / 40小时续航', 299.00, 120, 1, '主动降噪，支持双设备连接'),
('机械键盘 K3', '数码', '茶轴 / 87键 / RGB', 399.00, 0, 0, '热插拔轴体，三模连接'),
('纯棉T恤', '服饰', '白色 / L码', 79.00, 300, 1, '100%纯棉，透气舒适'),
('保温杯 500ml', '家居', '不锈钢 / 316内胆', 129.00, 88, 1, '24小时保温'),
('oopp15 手机', '手机', '8GB+256GB / 幻夜黑', 1500.00, 15, 1, '5G 全网通，6.7 英寸大屏，5000mAh 长续航');

INSERT INTO orders (order_no, user_id, order_time, pay_status, ship_status,
                    logistics_company, logistics_no, logistics_location,
                    receiver_name, receiver_area) VALUES
('2026112000001001', 1001, DATE_SUB(NOW(), INTERVAL 3 DAY), 1, 1,
 '顺丰速运', 'SF1234567890001', '深圳市转运中心', '张三', '广东省深圳市南山区'),
('2026111800001002', 1001, DATE_SUB(NOW(), INTERVAL 5 DAY), 1, 2,
 '京东物流', 'JD9876543210002', '已签收', '张三', '广东省深圳市南山区'),
('2026112100002001', 1002, DATE_SUB(NOW(), INTERVAL 2 DAY), 1, 0,
 NULL, NULL, NULL, '李四', '北京市朝阳区');

INSERT INTO order_items (order_id, product_id, product_name_snapshot, spec, num, price) VALUES
(1, 1, '降噪蓝牙耳机', '黑色 / 蓝牙5.3 / 40小时续航', 1, 299.00),
(2, 3, '纯棉T恤', '白色 / L码', 2, 79.00),
(3, 2, '机械键盘 K3', '茶轴 / 87键 / RGB', 1, 399.00);

-- ---------------------------
-- 生产环境只读账号建议（本地 compose 已由 MYSQL_USER 自动创建，
-- 但拥有全部权限；生产请按下面方式收紧为仅 SELECT）：
--
-- CREATE USER 'aics_ro'@'%' IDENTIFIED BY '强密码';
-- GRANT SELECT ON aics.v_order_ai_safe TO 'aics_ro'@'%';
-- GRANT SELECT ON aics.order_items TO 'aics_ro'@'%';
-- GRANT SELECT ON aics.products TO 'aics_ro'@'%';
-- FLUSH PRIVILEGES;
-- ---------------------------
