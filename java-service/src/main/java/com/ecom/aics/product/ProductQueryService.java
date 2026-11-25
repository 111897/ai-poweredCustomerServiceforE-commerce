package com.ecom.aics.product;

import com.ecom.aics.config.AppProperties;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 商品只读查询（按名称/类目关键词，参数化 LIKE）。
 */
@Service
public class ProductQueryService {

    private final JdbcTemplate jdbc;
    private final AppProperties props;

    public ProductQueryService(JdbcTemplate jdbc, AppProperties props) {
        this.jdbc = jdbc;
        this.props = props;
    }

    public List<ProductView> search(String keyword) {
        String kw = "%" + (keyword == null ? "" : keyword.trim()) + "%";
        String sql = """
                SELECT name, spec, price, stock_status
                FROM products
                WHERE name LIKE ? OR category LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """;
        return jdbc.query(sql, (rs, rowNum) -> new ProductView(
                rs.getString("name"),
                rs.getString("spec"),
                rs.getBigDecimal("price").toPlainString(),
                rs.getInt("stock_status") == 1 ? "有货" : "缺货"
        ), kw, kw, props.getProductLimit());
    }
}
