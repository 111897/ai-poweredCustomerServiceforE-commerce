from app.rag.router import route


def test_route_by_intent():
    assert route("order", "我买的耳机发货了吗") == ["faq"]
    assert route("product", "oopp15 多少钱") == ["product"]
    assert route("faq", "退换货政策") == ["faq"]
