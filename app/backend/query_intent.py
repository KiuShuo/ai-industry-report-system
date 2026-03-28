import re
from dataclasses import dataclass

from security_identifier import normalize_security_identifier


@dataclass(frozen=True)
class QueryIntent:
    raw_topic: str
    normalized_topic: str
    profile_hint: str
    ticker: str = ""
    security_code: str = ""
    company_hint: str = ""
    canonical_symbol: str = ""
    market: str = ""
    exchange: str = ""
    identifier_type: str = ""


EARNINGS_KEYWORDS = (
    "财报",
    "年报",
    "半年报",
    "中报",
    "季报",
    "一季报",
    "三季报",
    "业绩",
    "业绩预告",
    "业绩快报",
    "盈利预测",
    "业绩指引",
    "earnings",
    "guidance",
    "results",
    "quarterly report",
)

MACRO_KEYWORDS = (
    "宏观",
    "利率",
    "加息",
    "降息",
    "通胀",
    "cpi",
    "ppi",
    "pmi",
    "非农",
    "美债",
    "国债",
    "收益率",
    "原油",
    "黄金",
    "铜",
    "天然气",
    "煤炭",
    "汇率",
    "美元",
    "commodity",
    "commodities",
    "macro",
    "rates",
    "inflation",
    "oil",
    "gold",
    "copper",
)

STOCK_EVENT_KEYWORDS = (
    "个股",
    "股票",
    "公司公告",
    "上市公司",
    "问询函",
    "监管函",
    "ticker",
    "stock",
    "company news",
    "公告",
    "回购",
    "分红",
    "并购",
)

US_TICKER_PATTERN = re.compile(r"\b[A-Z]{1,5}\b")
CN_STOCK_CODE_PATTERN = re.compile(r"\b\d{6}\b")
HK_TICKER_PATTERN = re.compile(r"\b(?:0?\d{4,5})(?:\.HK|HK)?\b", re.IGNORECASE)


def _contains_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _extract_ticker(text: str) -> str:
    match = US_TICKER_PATTERN.search(text)
    return match.group(0) if match else ""


def _extract_cn_code(text: str) -> str:
    match = CN_STOCK_CODE_PATTERN.search(text)
    return match.group(0) if match else ""


def _extract_hk_ticker(text: str) -> str:
    match = HK_TICKER_PATTERN.search(text)
    if not match:
        return ""
    value = match.group(0).upper()
    return value if value.endswith(".HK") or value.endswith("HK") else f"{value}.HK"


def _clean_company_hint(text: str) -> str:
    stripped = text
    for keyword in EARNINGS_KEYWORDS + MACRO_KEYWORDS + STOCK_EVENT_KEYWORDS:
        stripped = stripped.replace(keyword, " ")
        stripped = stripped.replace(keyword.upper(), " ")
    stripped = US_TICKER_PATTERN.sub(" ", stripped)
    stripped = CN_STOCK_CODE_PATTERN.sub(" ", stripped)
    stripped = HK_TICKER_PATTERN.sub(" ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped


def infer_query_intent(topic: str) -> QueryIntent:
    raw_topic = (topic or "").strip()
    if not raw_topic:
        return QueryIntent(raw_topic="", normalized_topic="", profile_hint="")

    security = normalize_security_identifier(raw_topic)
    ticker = security.ticker or _extract_ticker(raw_topic)
    security_code = security.security_code or _extract_cn_code(raw_topic)
    hk_ticker = _extract_hk_ticker(raw_topic)
    company_hint = security.company_hint or _clean_company_hint(raw_topic)

    if _contains_keyword(raw_topic, MACRO_KEYWORDS):
        return QueryIntent(
            raw_topic=raw_topic,
            normalized_topic=raw_topic,
            profile_hint="macro-rates-commodities",
            ticker=ticker or hk_ticker,
            security_code=security_code,
            company_hint=company_hint,
            canonical_symbol=security.canonical_symbol,
            market=security.market,
            exchange=security.exchange,
            identifier_type=security.identifier_type,
        )

    if _contains_keyword(raw_topic, EARNINGS_KEYWORDS):
        normalized_parts = [part for part in [company_hint, security.canonical_symbol or ticker or hk_ticker, security_code, "earnings guidance results"] if part]
        return QueryIntent(
            raw_topic=raw_topic,
            normalized_topic=" ".join(normalized_parts) or raw_topic,
            profile_hint="earnings-and-guidance",
            ticker=ticker or hk_ticker,
            security_code=security_code,
            company_hint=company_hint,
            canonical_symbol=security.canonical_symbol,
            market=security.market,
            exchange=security.exchange,
            identifier_type=security.identifier_type,
        )

    if ticker or hk_ticker or security_code or _contains_keyword(raw_topic, STOCK_EVENT_KEYWORDS):
        normalized_parts = [part for part in [company_hint, security.canonical_symbol or ticker or hk_ticker, security_code, "company news filing listed company"] if part]
        return QueryIntent(
            raw_topic=raw_topic,
            normalized_topic=" ".join(normalized_parts) or raw_topic,
            profile_hint="ticker-company-news",
            ticker=ticker or hk_ticker,
            security_code=security_code,
            company_hint=company_hint,
            canonical_symbol=security.canonical_symbol,
            market=security.market,
            exchange=security.exchange,
            identifier_type=security.identifier_type,
        )

    return QueryIntent(
        raw_topic=raw_topic,
        normalized_topic=raw_topic,
        profile_hint="",
        ticker=ticker or hk_ticker,
        security_code=security_code,
        company_hint=company_hint,
        canonical_symbol=security.canonical_symbol,
        market=security.market,
        exchange=security.exchange,
        identifier_type=security.identifier_type,
    )
