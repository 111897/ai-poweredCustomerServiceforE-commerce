package com.ecom.aics.order;

import com.ecom.aics.config.AppProperties;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.atLeastOnce;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class OrderQueryServiceTest {

    @Test
    void usesMaskedViewByDefault() {
        JdbcTemplate jdbc = mock(JdbcTemplate.class);
        when(jdbc.query(anyString(), any(RowMapper.class), any(), any(), any(), any(), any()))
                .thenReturn(List.of());

        OrderQueryService service = new OrderQueryService(jdbc, new AppProperties());
        service.findRecentOrders(1001L, 10, "耳机");

        assertTrue(capturedSql(jdbc).stream().anyMatch(sql -> sql.contains("v_order_ai_safe")));
    }

    @Test
    void canFallbackToBaseTable() {
        JdbcTemplate jdbc = mock(JdbcTemplate.class);
        when(jdbc.query(anyString(), any(RowMapper.class), any(), any(), any(), any(), any()))
                .thenReturn(List.of());

        AppProperties props = new AppProperties();
        props.getOrderQuery().setUseView(false);
        OrderQueryService service = new OrderQueryService(jdbc, props);
        service.findRecentOrders(1001L, 10, "耳机");

        assertTrue(capturedSql(jdbc).stream().anyMatch(sql -> sql.contains("FROM orders")));
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static List<String> capturedSql(JdbcTemplate jdbc) {
        ArgumentCaptor<String> captor = ArgumentCaptor.forClass(String.class);
        verify(jdbc, atLeastOnce()).query(
                captor.capture(), any(RowMapper.class), any(), any(), any(), any(), any());
        return captor.getAllValues();
    }
}
