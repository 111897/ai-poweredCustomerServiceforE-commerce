"""歧义判定：规则兜底；非 Mock 模式下可叠加 LLM 判定。"""

_PRONOUNS = ("这个", "那个", "它", "该商品", "那件", "这款", "那款", "上面说的")


async def judge(message: str, has_context: bool, llm) -> tuple[bool, str]:
    """返回 (是否歧义, 澄清话术)。"""
    if not message:
        return True, ""

    if (any(p in message for p in _PRONOUNS)
            and not has_context
            and len(message) <= 12):
        return True, "您的问题可能有多种理解，能具体说一下是哪个商品或订单吗？"

    # 短句（如“我是否已经下单”“我的快递到哪里了”）购物意图明确，不交给模型判定，
    # 避免模型过度澄清；长句再叠加 LLM 判定。
    if not getattr(llm, "is_mock", True) and len(message) >= 12:
        try:
            answer = await llm.classify_ambiguity(message)
            if answer:
                return True, "您的问题可能有多种理解，能具体说明一下吗？"
        except Exception:
            pass
    return False, ""
