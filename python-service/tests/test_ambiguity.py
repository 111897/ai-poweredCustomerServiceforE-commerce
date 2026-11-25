import pytest

from app.compliance.ambiguity import judge


class FakeLlm:
    def __init__(self, is_mock: bool = True, answer: bool = False):
        self.is_mock = is_mock
        self.answer = answer

    async def classify_ambiguity(self, message: str) -> bool:
        return self.answer


@pytest.mark.asyncio
async def test_pronoun_without_context_is_ambiguous():
    ambiguous, text = await judge("这个多少钱", False, FakeLlm())
    assert ambiguous
    assert text


@pytest.mark.asyncio
async def test_short_message_skips_llm():
    ambiguous, _ = await judge(
        "我是否已经下单", True, FakeLlm(is_mock=False, answer=True))
    assert not ambiguous


@pytest.mark.asyncio
async def test_long_message_uses_llm():
    ambiguous, _ = await judge(
        "请详细说明一下这个商品的售后政策",
        True,
        FakeLlm(is_mock=False, answer=True),
    )
    assert ambiguous
