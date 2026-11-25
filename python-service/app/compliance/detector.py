"""违禁词检测（FR-05）：从 banned.xlsx 加载，normal 入 AC 自动机、regex 编译正则。"""

import logging
import re
from pathlib import Path

from openpyxl import load_workbook

from ..rag.schema_validator import canonical_header, validate_headers
from ..rag.templates import BANNED_REQUIRED

log = logging.getLogger(__name__)

try:
    import ahocorasick  # noqa: F401
except ImportError:  # 未安装时降级为线性匹配
    ahocorasick = None


class BannedDetector:
    def __init__(self, banned_dir: str):
        self.patterns: list[str] = []
        self.regexes: list[re.Pattern] = []
        self._automaton = None
        self.load(banned_dir)

    def load(self, banned_dir: str) -> None:
        path = Path(banned_dir) / "banned.xlsx"
        self.patterns, self.regexes = [], []
        if not path.exists():
            log.warning("违禁词文件不存在: %s", path)
            self._rebuild()
            return

        wb = load_workbook(path, read_only=True, data_only=True)
        try:
            values = list(wb.active.iter_rows(values_only=True))
        finally:
            wb.close()
        if not values:
            self._rebuild()
            return

        headers = [canonical_header(c) for c in values[0]]
        ok, missing = validate_headers(headers, BANNED_REQUIRED)
        if not ok:
            log.warning("违禁词表缺少必填列 %s，尝试按列名解析", missing)

        index = {h: i for i, h in enumerate(headers)}
        p_idx = index.get("pattern", 0)
        t_idx = index.get("type", 1)

        for row in values[1:]:
            if row is None or len(row) <= p_idx or row[p_idx] is None:
                continue
            pattern = str(row[p_idx]).strip()
            if not pattern:
                continue
            kind = (str(row[t_idx]).strip().lower()
                    if len(row) > t_idx and row[t_idx] else "normal")
            if kind == "regex":
                try:
                    self.regexes.append(re.compile(pattern))
                except re.error as exc:
                    log.warning("正则违禁词编译失败 %s: %s", pattern, exc)
            else:
                self.patterns.append(pattern)

        self._rebuild()
        log.info("违禁词已加载：普通词 %d 条，正则 %d 条",
                 len(self.patterns), len(self.regexes))

    def _rebuild(self) -> None:
        if ahocorasick and self.patterns:
            self._automaton = ahocorasick.Automaton()
            for pattern in self.patterns:
                self._automaton.add_word(pattern, pattern)
            self._automaton.make_automaton()
        else:
            self._automaton = None

    def scan(self, text: str) -> list[str]:
        if not text:
            return []
        hits: set[str] = set()
        if self._automaton is not None:
            hits.update(value for _, value in self._automaton.iter(text))
        else:
            hits.update(p for p in self.patterns if p in text)
        for regex in self.regexes:
            if regex.search(text):
                hits.add(regex.pattern)
        return sorted(hits)
