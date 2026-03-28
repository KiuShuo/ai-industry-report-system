import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Dict, Iterable, List, Sequence
from urllib.parse import urljoin, urlparse

from http_client import request_json
from query_intent import QueryIntent, infer_query_intent
from settings import get_settings


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
GENERIC_STOP_WORDS = {
    "行业",
    "市场",
    "资讯",
    "动态",
    "研究",
    "报告",
    "最近",
    "近",
    "最新",
    "数据",
    "情况",
    "分析",
    "company",
    "news",
    "industry",
    "market",
    "latest",
    "report",
    "guidance",
    "results",
    "filing",
    "listed",
}
DATE_PATTERN = re.compile(
    r"(20\d{2}[./-]\d{1,2}[./-]\d{1,2}|20\d{2}年\d{1,2}月\d{1,2}日|\d{2}[./-]\d{2})"
)
ANCHOR_PATTERN = re.compile(
    r'<a[^>]+href=["\'](?P<link>[^"\']+)["\'][^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class OfficialSourceDefinition:
    name: str
    label: str
    category: str
    urls: Sequence[str]
    profile_hints: Sequence[str] = field(default_factory=tuple)
    priority: int = 100
    title_keywords: Sequence[str] = field(default_factory=tuple)


OFFICIAL_SOURCES: Sequence[OfficialSourceDefinition] = (
    OfficialSourceDefinition(
        name="cninfo",
        label="巨潮资讯",
        category="official-disclosure",
        urls=("https://www.cninfo.com.cn/",),
        profile_hints=("ticker-company-news", "earnings-and-guidance", "stock-industry-news", "generic-industry"),
        priority=5,
        title_keywords=(
            "公告",
            "年报",
            "半年报",
            "季报",
            "业绩预告",
            "业绩快报",
            "分红",
            "回购",
            "问询函",
            "监管",
        ),
    ),
    OfficialSourceDefinition(
        name="stats",
        label="国家统计局",
        category="official-statistics",
        urls=(
            "https://www.stats.gov.cn/sj/zxfb/rss.xml",
            "https://www.stats.gov.cn/sj/sjjd/rss.xml",
        ),
        profile_hints=("macro-rates-commodities", "stock-industry-news", "generic-industry"),
        priority=10,
        title_keywords=("统计", "工业", "制造业", "消费", "投资", "价格", "cpi", "ppi", "pmi"),
    ),
    OfficialSourceDefinition(
        name="csrc",
        label="中国证监会",
        category="official-regulation",
        urls=("https://www.csrc.gov.cn/csrc/c100040/common_list.shtml",),
        profile_hints=("ticker-company-news", "earnings-and-guidance", "stock-industry-news"),
        priority=20,
        title_keywords=("证监会", "监管", "证券", "上市公司", "行政处罚", "监管措施", "信息披露"),
    ),
    OfficialSourceDefinition(
        name="sse",
        label="上海证券交易所",
        category="exchange-disclosure",
        urls=(
            "https://www.sse.com.cn/aboutus/mediacenter/hotandd/",
            "https://www.sse.com.cn/aboutus/mediacenter/conference/",
        ),
        profile_hints=("ticker-company-news", "earnings-and-guidance", "stock-industry-news"),
        priority=25,
        title_keywords=(
            "上交所",
            "沪市",
            "上市公司",
            "再融资",
            "信息披露",
            "监管",
            "风险提示",
            "年报",
            "季报",
        ),
    ),
    OfficialSourceDefinition(
        name="szse",
        label="深圳证券交易所",
        category="exchange-disclosure",
        urls=(
            "https://www.szse.cn/www/aboutus/",
            "https://www.szse.cn/disclosure/notice/general/index.html",
        ),
        profile_hints=("ticker-company-news", "earnings-and-guidance", "stock-industry-news"),
        priority=26,
        title_keywords=(
            "深交所",
            "深市",
            "上市公司",
            "创业板",
            "信息披露",
            "监管",
            "风险提示",
            "年报",
            "季报",
        ),
    ),
    OfficialSourceDefinition(
        name="miit",
        label="工业和信息化部",
        category="official-industry",
        urls=("https://wap.miit.gov.cn/",),
        profile_hints=("generic-industry", "stock-industry-news"),
        priority=30,
        title_keywords=("工业", "制造业", "汽车", "软件", "电子", "通信", "互联网", "造船", "新能源"),
    ),
    OfficialSourceDefinition(
        name="safe",
        label="国家外汇管理局",
        category="official-macro",
        urls=("https://m.safe.gov.cn/safe/whcb/index.html",),
        profile_hints=("macro-rates-commodities", "stock-industry-news", "generic-industry"),
        priority=40,
        title_keywords=("外汇", "储备", "国际收支", "结售汇", "汇率"),
    ),
    OfficialSourceDefinition(
        name="customs",
        label="海关总署",
        category="official-trade",
        urls=("https://english.customs.gov.cn/Statistics/Statistics?ColumnId=3",),
        profile_hints=("macro-rates-commodities", "stock-industry-news", "generic-industry"),
        priority=50,
        title_keywords=("trade", "import", "export", "foreign trade", "imports", "exports"),
    ),
    OfficialSourceDefinition(
        name="bse",
        label="北京证券交易所",
        category="exchange-disclosure",
        urls=(
            "https://www.bse.cn/important_news/",
            "https://www.bse.cn/company/info_public.html",
            "https://www.bse.cn/disclosure/vocational.html",
        ),
        profile_hints=("ticker-company-news", "earnings-and-guidance", "stock-industry-news"),
        priority=55,
        title_keywords=(
            "北交所",
            "上市公司",
            "信息披露",
            "公告",
            "年报",
            "季报",
            "监管",
        ),
    ),
)
OFFICIAL_SOURCE_MAP = {item.name: item for item in OFFICIAL_SOURCES}


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _source_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url


def _normalize_date(raw_value: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""

    try:
        parsed = parsedate_to_datetime(value)
        return parsed.date().isoformat()
    except (TypeError, ValueError, IndexError, OverflowError):
        pass

    normalized = value.replace(".", "-").replace("/", "-").replace("年", "-").replace("月", "-").replace("日", "")
    for pattern in ("%Y-%m-%d", "%m-%d"):
        try:
            parsed = datetime.strptime(normalized, pattern)
            if pattern == "%m-%d":
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.date().isoformat()
        except ValueError:
            continue
    return value


def _time_range_days(time_range: str) -> int:
    normalized = (time_range or "").strip().lower()
    if normalized.endswith("d") and normalized[:-1].isdigit():
        return int(normalized[:-1])
    return {
        "day": 1,
        "week": 7,
        "month": 30,
        "quarter": 90,
        "year": 365,
    }.get(normalized, 365)


def _within_time_range(published_date: str, time_range: str) -> bool:
    normalized = _normalize_date(published_date)
    if not normalized:
        return True
    try:
        published = datetime.strptime(normalized, "%Y-%m-%d").date()
    except ValueError:
        return True
    return published >= date.today() - timedelta(days=max(_time_range_days(time_range) - 1, 0))


def _topic_tokens(topic: str, intent: QueryIntent, source: OfficialSourceDefinition) -> List[str]:
    raw_tokens: List[str] = []
    raw_tokens.extend(re.findall(r"[\u4e00-\u9fff]{2,}", topic or ""))
    raw_tokens.extend(re.findall(r"[A-Za-z]{3,}", topic or ""))
    raw_tokens.extend(re.findall(r"\d{6}", topic or ""))

    for extra in (
        intent.normalized_topic,
        intent.company_hint,
        intent.ticker,
        intent.security_code,
        intent.canonical_symbol,
    ):
        if not extra:
            continue
        raw_tokens.extend(re.findall(r"[\u4e00-\u9fff]{2,}", extra))
        raw_tokens.extend(re.findall(r"[A-Za-z]{2,}", extra))
        raw_tokens.extend(re.findall(r"\d{4,6}", extra))

    tokens: List[str] = []
    source_text = f"{topic or ''} {intent.normalized_topic or ''}".lower()
    matched_source_keywords = [keyword for keyword in source.title_keywords if keyword.lower() in source_text]

    for token in list(raw_tokens) + matched_source_keywords:
        cleaned = token.strip().lower()
        if len(cleaned) < 2 or cleaned in GENERIC_STOP_WORDS:
            continue
        if cleaned not in tokens:
            tokens.append(cleaned)
    return tokens


def _relevance_score(item: Dict[str, str], tokens: Sequence[str]) -> int:
    title = (item.get("title") or "").lower()
    summary = (item.get("summary") or "").lower()
    haystack = f"{title} {summary}"
    return sum(2 if token in title else 1 for token in tokens if token in haystack)


def _parse_rss_items(xml_text: str, source: OfficialSourceDefinition) -> List[Dict[str, str]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    items: List[Dict[str, str]] = []
    for node in root.findall(".//item"):
        title = _strip_html(node.findtext("title", ""))
        link = (node.findtext("link", "") or "").strip()
        published = _normalize_date(node.findtext("pubDate", ""))
        description = _strip_html(node.findtext("description", ""))
        if not title or not link:
            continue
        items.append(
            {
                "title": title,
                "summary": description,
                "rawContent": description,
                "source": source.label,
                "category": source.category,
                "url": link,
                "publishedDate": published,
                "sourceBackend": "official",
                "sourceChannel": source.name,
            }
        )
    return items


def _extract_anchor_items(html_text: str, source: OfficialSourceDefinition, base_url: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    seen = set()
    for match in ANCHOR_PATTERN.finditer(html_text or ""):
        href = (match.group("link") or "").strip()
        if not href or href.startswith("javascript:") or href.startswith("#"):
            continue
        title = _strip_html(match.group("title") or "")
        if len(title) < 6:
            continue

        window = html_text[max(0, match.start() - 80): min(len(html_text), match.end() + 260)]
        date_match = DATE_PATTERN.search(window)
        if not date_match:
            continue
        published = _normalize_date(date_match.group(1))
        link = urljoin(base_url, href)
        dedupe_key = (title, link, published)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        summary = f"{source.label}公开发布信息，发布时间 {published or '未知'}。"
        items.append(
            {
                "title": title,
                "summary": summary,
                "rawContent": summary,
                "source": source.label,
                "category": source.category,
                "url": link,
                "publishedDate": published,
                "sourceBackend": "official",
                "sourceChannel": source.name,
            }
        )
    return items


class OfficialPublicSourceConnector:
    def __init__(self):
        self.settings = get_settings()

    def is_enabled(self) -> bool:
        return self.settings.enable_official_sources and bool(self.active_sources())

    def active_sources(self) -> List[OfficialSourceDefinition]:
        names = self.settings.official_source_names
        if not names:
            return list(OFFICIAL_SOURCES)
        sources: List[OfficialSourceDefinition] = []
        for name in names:
            source = OFFICIAL_SOURCE_MAP.get(name)
            if source is not None:
                sources.append(source)
        return sources

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/html,application/xml,text/xml;q=0.9,*/*;q=0.8",
        }

    def _fetch_text(self, url: str) -> str:
        response = request_json("GET", url, headers=self._headers(), timeout=self.settings.official_source_timeout)
        response.raise_for_status()
        return response.text

    def _fetch_source_items(self, source: OfficialSourceDefinition) -> List[Dict[str, str]]:
        collected: List[Dict[str, str]] = []
        for url in source.urls:
            try:
                text = self._fetch_text(url)
            except Exception:
                continue
            if url.endswith(".xml"):
                collected.extend(_parse_rss_items(text, source))
            else:
                collected.extend(_extract_anchor_items(text, source, url))
        return collected

    def _source_matches_intent(self, source: OfficialSourceDefinition, intent: QueryIntent) -> bool:
        if not source.profile_hints:
            return True
        if not intent.profile_hint:
            return True
        return intent.profile_hint in source.profile_hints

    def _rank_and_filter(
        self,
        items: Iterable[Dict[str, str]],
        source: OfficialSourceDefinition,
        topic: str,
        time_range: str,
        intent: QueryIntent,
    ) -> List[Dict[str, str]]:
        tokens = _topic_tokens(topic, intent, source)
        ranked: List[tuple[int, Dict[str, str]]] = []
        for item in items:
            if not _within_time_range(item.get("publishedDate", ""), time_range):
                continue
            score = _relevance_score(item, tokens)
            if tokens and score == 0:
                continue
            ranked.append((score, item))

        ranked.sort(
            key=lambda pair: (
                pair[0],
                _normalize_date(pair[1].get("publishedDate", "")),
            ),
            reverse=True,
        )
        return [item for _, item in ranked]

    def search(self, topic: str, time_range: str = "7d", max_results: int = 6) -> List[Dict[str, str]]:
        if not self.is_enabled():
            return []

        intent = infer_query_intent(topic)
        selected_sources = [
            source for source in self.active_sources()
            if self._source_matches_intent(source, intent)
        ]
        if not selected_sources:
            selected_sources = self.active_sources()

        per_source_limit = max(1, self.settings.official_source_max_results)
        collected: List[Dict[str, str]] = []
        seen = set()
        for source in sorted(selected_sources, key=lambda item: item.priority):
            source_items = self._rank_and_filter(self._fetch_source_items(source), source, topic, time_range, intent)
            for item in source_items[:per_source_limit]:
                dedupe_key = (item.get("title", ""), item.get("url", ""))
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                collected.append(item)
                if len(collected) >= max_results:
                    return collected
        return collected
