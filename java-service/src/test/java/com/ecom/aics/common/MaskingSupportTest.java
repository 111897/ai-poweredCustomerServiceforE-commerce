package com.ecom.aics.common;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class MaskingSupportTest {

    @Test
    void maskOrderNoKeepsLastFour() {
        assertEquals("****1001", MaskingSupport.maskOrderNo("2026112000001001"));
        assertEquals("****1001", MaskingSupport.maskOrderNo("****1001"));
        assertEquals("****", MaskingSupport.maskOrderNo(null));
        assertEquals("****", MaskingSupport.maskOrderNo("123"));
    }

    @Test
    void truncateAreaKeepsDistrict() {
        assertEquals("广东省深圳市南山区",
                MaskingSupport.truncateArea("广东省深圳市南山区科技园"));
        assertEquals("北京市朝阳区",
                MaskingSupport.truncateArea("北京市朝阳区建国路88号"));
        assertEquals("上海市浦东新区",
                MaskingSupport.truncateArea("上海市浦东新区"));
    }

    @Test
    void truncateAreaHidesUnrecognizedAddress() {
        assertEquals("**", MaskingSupport.truncateArea("某街道园区"));
        assertEquals("**", MaskingSupport.truncateArea("朝阳区建国路"));
        assertEquals("", MaskingSupport.truncateArea(""));
    }

    @Test
    void shipStatusText() {
        assertEquals("未发货", MaskingSupport.shipStatusText(0));
        assertEquals("已发货", MaskingSupport.shipStatusText(1));
        assertEquals("已签收", MaskingSupport.shipStatusText(2));
        assertEquals("未知状态", MaskingSupport.shipStatusText(9));
    }
}
