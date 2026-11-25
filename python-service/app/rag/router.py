"""意图路由：按意图将检索定向到业务子库；低置信并行双库。"""

ORDER_KEYWORDS = ("订单", "发货", "物流", "快递", "签收", "我的单", "退款")
PRODUCT_KEYWORDS = ("价格", "多少钱", "规格", "库存", "有货", "商品", "款式", "颜色")
FAQ_KEYWORDS = ("政策", "规则", "售后", "换货", "保修", "怎么退")


def route(intent: str, message: str) -> list[str]:
    if intent == "order":
        # 订单信息以实时数据为准，知识库侧用 faq 补充政策；商品信息走 product
        return ["faq"]
    if intent == "product":
        return ["product"]
    if intent == "faq":
        return ["faq"]

    text = message or ""
    if any(k in text for k in PRODUCT_KEYWORDS):
        return ["product", "faq"]
    if any(k in text for k in FAQ_KEYWORDS):
        return ["faq"]
    return ["faq", "product"]
