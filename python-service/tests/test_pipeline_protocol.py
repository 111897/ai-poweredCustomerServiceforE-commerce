import pytest
from openpyxl import Workbook

from app.compliance.detector import BannedDetector
from app.orchestrator import pipeline


def _write_banned(path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "data"
    sheet.append(["pattern", "type", "note"])
    sheet.append(["代开发票", "normal", "违规服务"])
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def _event_names(events: list[str]) -> list[str]:
    return [event.split("\n")[0].removeprefix("event: ") for event in events]


@pytest.mark.asyncio
async def test_banned_message_is_wrapped_in_segments(tmp_path):
    _write_banned(tmp_path / "banned.xlsx")
    detector = BannedDetector(str(tmp_path))
    pipeline.init_dependencies(None, detector)

    events = [event async for event in pipeline._run(
        1, "s-banned", "你好，帮我代开发票", "", "trace-banned")]

    assert _event_names(events) == [
        "start", "warning", "segment", "delta", "segment_end", "done"]
    assert '"finishReason": "blocked"' in events[-1]


@pytest.mark.asyncio
async def test_out_of_scope_message_is_wrapped_in_segments():
    pipeline.init_dependencies(None, None)

    events = [event async for event in pipeline._run(
        1, "s-scope", "帮我写一段 Java 代码", "", "trace-scope")]

    assert _event_names(events) == [
        "start", "warning", "segment", "delta", "segment_end", "done"]
    assert '"finishReason": "blocked"' in events[-1]
