import re
from dataclasses import dataclass


US_SYMBOL_PATTERN = re.compile(r"\b(?:NASDAQ|NYSE|AMEX):([A-Z]{1,5})\b|\b([A-Z]{1,5})\b")
CN_SYMBOL_PATTERN = re.compile(r"\b(?:SHSE|SSE|SZSE|BSE):(\d{6})\b|\b(\d{6})\b")
HK_SYMBOL_PATTERN = re.compile(r"\b(?:HKEX|SEHK):([0-9]{4,5})\b|\b([0-9]{4,5})(?:\.HK|HK)\b", re.IGNORECASE)


@dataclass(frozen=True)
class SecurityIdentifier:
    input_text: str = ""
    symbol: str = ""
    market: str = ""
    exchange: str = ""
    identifier_type: str = ""
    ticker: str = ""
    security_code: str = ""
    company_hint: str = ""

    @property
    def canonical_symbol(self) -> str:
        if self.exchange and self.symbol:
            return f"{self.exchange}:{self.symbol}"
        return self.symbol


def _normalize_cn_exchange(code: str) -> tuple[str, str]:
    if code.startswith(("600", "601", "603", "605", "688", "689", "900")):
        return "CN", "SHSE"
    if code.startswith(("000", "001", "002", "003", "300", "301", "200")):
        return "CN", "SZSE"
    if code.startswith(("430", "440", "830", "831", "832", "833", "834", "835", "836", "837", "838", "839", "870", "871", "872", "873", "874", "875", "876", "877", "878", "879")):
        return "CN", "BSE"
    return "CN", "CN"


def _strip_security_tokens(text: str) -> str:
    stripped = US_SYMBOL_PATTERN.sub(" ", text)
    stripped = CN_SYMBOL_PATTERN.sub(" ", stripped)
    stripped = HK_SYMBOL_PATTERN.sub(" ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped


def normalize_security_identifier(topic: str) -> SecurityIdentifier:
    raw_topic = (topic or "").strip()
    if not raw_topic:
        return SecurityIdentifier()

    hk_match = HK_SYMBOL_PATTERN.search(raw_topic)
    if hk_match:
        raw_code = hk_match.group(1) or hk_match.group(2) or ""
        normalized_code = raw_code.zfill(4)
        company_hint = _strip_security_tokens(raw_topic)
        return SecurityIdentifier(
            input_text=raw_topic,
            symbol=normalized_code,
            market="HK",
            exchange="HKEX",
            identifier_type="ticker",
            ticker=f"{normalized_code}.HK",
            security_code=normalized_code,
            company_hint=company_hint,
        )

    cn_match = CN_SYMBOL_PATTERN.search(raw_topic)
    if cn_match:
        raw_code = cn_match.group(1) or cn_match.group(2) or ""
        market, exchange = _normalize_cn_exchange(raw_code)
        company_hint = _strip_security_tokens(raw_topic)
        return SecurityIdentifier(
            input_text=raw_topic,
            symbol=raw_code,
            market=market,
            exchange=exchange,
            identifier_type="security_code",
            ticker=raw_code,
            security_code=raw_code,
            company_hint=company_hint,
        )

    us_match = US_SYMBOL_PATTERN.search(raw_topic)
    if us_match:
        raw_ticker = us_match.group(1) or us_match.group(2) or ""
        upper_ticker = raw_ticker.upper()
        company_hint = _strip_security_tokens(raw_topic)
        exchange = "US"
        if "NASDAQ:" in raw_topic.upper():
            exchange = "NASDAQ"
        elif "NYSE:" in raw_topic.upper():
            exchange = "NYSE"
        elif "AMEX:" in raw_topic.upper():
            exchange = "AMEX"
        return SecurityIdentifier(
            input_text=raw_topic,
            symbol=upper_ticker,
            market="US",
            exchange=exchange,
            identifier_type="ticker",
            ticker=upper_ticker,
            security_code="",
            company_hint=company_hint,
        )

    return SecurityIdentifier(
        input_text=raw_topic,
        company_hint=raw_topic,
        identifier_type="company_name",
    )
