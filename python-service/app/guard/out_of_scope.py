"""越界判定（规则 + 关键词兜底；非 Mock 时可叠加 LLM 分类）。"""

OUT_OF_SCOPE_KEYWORDS = (
    "政治", "选举", "医疗", "诊断", "药方", "股票", "基金", "法律",
    "写代码", "python", "java", "sql", "写诗", "小说", "翻译", "论文",
    "别人的订单", "其他用户", "系统提示", "忽略以上", "开发者模式",
    "管理员密码", "越狱",
)


def is_out_of_scope(message: str) -> bool:
    text = (message or "").lower()
    return any(keyword.lower() in text for keyword in OUT_OF_SCOPE_KEYWORDS)
