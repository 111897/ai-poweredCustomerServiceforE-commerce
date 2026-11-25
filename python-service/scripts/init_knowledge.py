"""初始化知识库 xlsx 模板与示例数据（在项目根目录执行）。

用法：
    python python-service/scripts/init_knowledge.py [--force]
"""

import argparse
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]  # 项目根目录
BASE = ROOT / "data" / "knowledge"

FAQ_HEADERS = ["id", "question", "answer", "category", "updated_at"]
PRODUCT_HEADERS = [
    "product_id", "name", "category", "spec",
    "price", "stock_status", "selling_points", "updated_at",
]
BANNED_HEADERS = ["pattern", "type", "note"]

FAQ_ROWS = [
    [1, "退换货政策是什么？", "平台支持七天无理由退换货，商品需保持完好。质量问题可申请免费换货。", "售后", "2026-11-01"],
    [2, "多久发货？", "一般下单后 48 小时内发货，偏远地区可能顺延。", "物流", "2026-11-01"],
    [3, "怎么联系人工客服？", "可在订单详情页点击“联系客服”转人工。", "售后", "2026-11-01"],
    [4, "支持货到付款吗？", "部分地区支持货到付款，以结算页展示为准。", "支付", "2026-11-01"],
]

PRODUCT_ROWS = [
    ["P1001", "降噪蓝牙耳机", "数码", "黑色 / 蓝牙5.3 / 40小时续航", "299.00", "有货", "主动降噪，双设备连接", "2026-11-01"],
    ["P1002", "机械键盘 K3", "数码", "茶轴 / 87键 / RGB", "399.00", "缺货", "热插拔轴体，三模连接", "2026-11-01"],
    ["P1003", "纯棉T恤", "服饰", "白色 / L码", "79.00", "有货", "100%纯棉，透气舒适", "2026-11-01"],
    ["P1004", "保温杯 500ml", "家居", "不锈钢 / 316内胆", "129.00", "有货", "24小时保温", "2026-11-01"],
]

BANNED_ROWS = [
    ["诈骗", "normal", "违法内容"],
    ["赌博", "normal", "违法内容"],
    ["代开发票", "normal", "违规服务"],
    ["忽略以上指令", "normal", "提示注入"],
    [r"\d{15,19}", "regex", "疑似身份证/银行卡长数字"],
    [r"1[3-9]\d{9}", "regex", "疑似手机号"],
]


def write_xlsx(path: Path, headers: list[str], rows: list[list], force: bool) -> None:
    if path.exists() and not force:
        print(f"[skip] {path.relative_to(ROOT)} 已存在（使用 --force 覆盖）")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "data"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)
    print(f"[ok] {path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化知识库 xlsx 模板")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的文件")
    args = parser.parse_args()

    write_xlsx(BASE / "faq" / "faq.xlsx", FAQ_HEADERS, FAQ_ROWS, args.force)
    write_xlsx(BASE / "product" / "product.xlsx", PRODUCT_HEADERS, PRODUCT_ROWS, args.force)
    write_xlsx(BASE / "banned" / "banned.xlsx", BANNED_HEADERS, BANNED_ROWS, args.force)
    print("知识库初始化完成。")


if __name__ == "__main__":
    main()
