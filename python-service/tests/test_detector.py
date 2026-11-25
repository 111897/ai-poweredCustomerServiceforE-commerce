from openpyxl import Workbook

from app.compliance.detector import BannedDetector


def _write_banned(path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "data"
    sheet.append(["pattern", "type", "note"])
    sheet.append(["代开发票", "normal", "违规服务"])
    sheet.append([r"\d{15,19}", "regex", "疑似长数字"])
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def test_normal_and_regex_hits(tmp_path):
    _write_banned(tmp_path / "banned.xlsx")
    detector = BannedDetector(str(tmp_path))

    assert detector.scan("你好，帮我代开发票") == ["代开发票"]
    assert detector.scan("卡号 1234567890123456") == [r"\d{15,19}"]
    assert detector.scan("你好") == []


def test_missing_file_is_safe(tmp_path):
    detector = BannedDetector(str(tmp_path))
    assert detector.scan("任意内容") == []
