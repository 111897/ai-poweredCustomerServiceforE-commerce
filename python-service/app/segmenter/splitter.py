"""回答分段器（FR-11）：单段 ≤ max_chars，按段落/语义断点切分，跨 chunk 累积。"""

_SEPARATORS = ("\n", "。", "！", "？", "；")


class Segmenter:
    """流式分段状态机：feed() 输入 token 增量，返回可发送的完整段。"""

    def __init__(self, max_chars: int = 200):
        self.max_chars = max_chars
        self.buffer = ""

    def feed(self, text: str) -> list[str]:
        self.buffer += text
        out: list[str] = []
        while True:
            seg = self._try_cut()
            if seg is None:
                break
            out.append(seg)
        return out

    def flush(self) -> list[str]:
        remainder = self.buffer.strip()
        self.buffer = ""
        return [remainder] if remainder else []

    def _try_cut(self) -> str | None:
        if len(self.buffer) > self.max_chars:
            window = self.buffer[: self.max_chars]
            # 1) 优先在窗口内最后的段落/语义断点处切
            for sep in _SEPARATORS:
                idx = window.rfind(sep)
                if idx != -1:
                    seg = self.buffer[: idx + 1].strip()
                    self.buffer = self.buffer[idx + 1:]
                    return seg or None
            # 2) 单句超长：窗口末尾软切，避免切在空白处
            cut = self.max_chars
            while cut > self.max_chars - 20 and cut > 0 and self.buffer[cut - 1].isspace():
                cut -= 1
            seg = self.buffer[:cut].strip()
            self.buffer = self.buffer[cut:]
            return seg or None
        # 未达上限时，遇到完整段落（换行）可提前切段
        idx = self.buffer.find("\n")
        if idx != -1:
            seg = self.buffer[: idx + 1].strip()
            self.buffer = self.buffer[idx + 1:]
            return seg or None
        return None
