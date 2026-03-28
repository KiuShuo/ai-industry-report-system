from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SearchProfile:
    name: str
    description: str
    match_keywords: List[str] = field(default_factory=list)
    tavily_topic: str = "news"
    query_hint: str = "latest industry updates market trends policies financing activity"
    include_domains: List[str] = field(default_factory=list)
    exclude_domains: List[str] = field(default_factory=list)
    exact_match: bool = False


GENERIC_PROFILE = SearchProfile(
    name="generic-industry",
    description="Default profile for broad industry monitoring and report generation.",
)


SHIPPING_FINANCE_PROFILE = SearchProfile(
    name="shipping-finance-leasing",
    description="Profile for maritime finance, shipping leasing, and vessel funding topics.",
    match_keywords=[
        "航运融资租赁",
        "船舶融资租赁",
        "航运租赁",
        "船舶租赁",
        "shipping finance",
        "ship finance",
        "ship leasing",
        "maritime leasing",
        "maritime finance",
    ],
    tavily_topic="news",
    query_hint=(
        "shipping finance ship leasing maritime leasing vessel funding sale and leaseback "
        "charter market shipowner financing policy"
    ),
    include_domains=[
        "lloydslist.com",
        "seatrade-maritime.com",
        "maritime-executive.com",
        "marinelink.com",
        "sinoshipnews.com",
        "hellenicshippingnews.com",
        "sse.net.cn",
        "szse.cn",
        "gov.cn",
        "stats.gov.cn",
    ],
    exclude_domains=[
        "baike.baidu.com",
        "linkedin.com",
        "zhidao.baidu.com",
    ],
)


STOCK_INDUSTRY_NEWS_PROFILE = SearchProfile(
    name="stock-industry-news",
    description="Profile for equity investors tracking industry trends, demand cycles, policy moves, and listed-company sector news.",
    match_keywords=[
        "行业资讯",
        "行业研究",
        "产业链",
        "景气度",
        "板块机会",
        "赛道",
        "行业动态",
        "sector",
        "industry news",
        "equity industry",
    ],
    tavily_topic="finance",
    query_hint=(
        "china a-share listed companies sector industry chain demand pricing policy earnings capacity "
        "supply chain market share regulation official disclosure"
    ),
    include_domains=[
        "cninfo.com.cn",
        "csrc.gov.cn",
        "gov.cn",
        "cs.com.cn",
        "cnstock.com",
        "stcn.com",
        "bse.cn",
        "sse.com.cn",
        "szse.cn",
        "stats.gov.cn",
        "miit.gov.cn",
        "safe.gov.cn",
        "customs.gov.cn",
    ],
    exclude_domains=[
        "baike.baidu.com",
        "linkedin.com",
        "zhidao.baidu.com",
    ],
)


TICKER_COMPANY_NEWS_PROFILE = SearchProfile(
    name="ticker-company-news",
    description="Profile for company-level listed-stock news, corporate events, and filing-related developments.",
    match_keywords=[
        "个股",
        "股票新闻",
        "公司公告",
        "上市公司",
        "ticker",
        "company news",
        "stock news",
        "earnings call",
        "guidance",
    ],
    tavily_topic="finance",
    query_hint=(
        "china a-share company announcement disclosure quarterly report annual report earnings guidance "
        "exchange inquiry regulatory letter buyback dividends merger acquisition"
    ),
    include_domains=[
        "cninfo.com.cn",
        "csrc.gov.cn",
        "cs.com.cn",
        "cnstock.com",
        "stcn.com",
        "bse.cn",
        "sse.com.cn",
        "szse.cn",
    ],
    exclude_domains=[
        "baike.baidu.com",
        "linkedin.com",
    ],
    exact_match=True,
)


EARNINGS_AND_GUIDANCE_PROFILE = SearchProfile(
    name="earnings-and-guidance",
    description="Profile for earnings releases, guidance revisions, calendars, and analyst estimate related news.",
    match_keywords=[
        "财报",
        "年报",
        "半年报",
        "中报",
        "季报",
        "一季报",
        "三季报",
        "业绩预告",
        "业绩快报",
        "盈利预测",
        "业绩指引",
        "earnings",
        "guidance",
        "results",
        "quarterly report",
    ],
    tavily_topic="finance",
    query_hint=(
        "china a-share quarterly report annual report earnings preannouncement performance express guidance "
        "estimate revision revenue profit margin official disclosure"
    ),
    include_domains=[
        "cninfo.com.cn",
        "csrc.gov.cn",
        "cs.com.cn",
        "cnstock.com",
        "stcn.com",
        "bse.cn",
        "sse.com.cn",
        "szse.cn",
    ],
    exclude_domains=[
        "baike.baidu.com",
        "linkedin.com",
    ],
)


MACRO_RATES_COMMODITIES_PROFILE = SearchProfile(
    name="macro-rates-commodities",
    description="Profile for macro, interest rates, inflation, FX, and commodity market developments relevant to investors.",
    match_keywords=[
        "宏观",
        "利率",
        "加息",
        "降息",
        "通胀",
        "非农",
        "cpi",
        "ppi",
        "pmi",
        "美债",
        "国债",
        "收益率",
        "原油",
        "黄金",
        "铜价",
        "天然气",
        "汇率",
        "美元",
        "commodity",
        "macro",
        "rates",
        "inflation",
        "oil",
        "gold",
        "copper",
    ],
    tavily_topic="finance",
    query_hint=(
        "macro economy inflation rates central bank treasury yield FX commodities oil gold copper natural gas "
        "policy outlook supply demand"
    ),
    include_domains=[
        "federalreserve.gov",
        "ecb.europa.eu",
        "imf.org",
        "worldbank.org",
        "bls.gov",
        "bea.gov",
        "eia.gov",
        "opec.org",
        "reuters.com",
        "bloomberg.com",
        "wsj.com",
        "marketwatch.com",
        "stlouisfed.org",
        "gov.cn",
        "stats.gov.cn",
        "pbc.gov.cn",
    ],
    exclude_domains=[
        "baike.baidu.com",
        "linkedin.com",
    ],
)


BUILTIN_SEARCH_PROFILES = [
    MACRO_RATES_COMMODITIES_PROFILE,
    EARNINGS_AND_GUIDANCE_PROFILE,
    TICKER_COMPANY_NEWS_PROFILE,
    STOCK_INDUSTRY_NEWS_PROFILE,
    SHIPPING_FINANCE_PROFILE,
    GENERIC_PROFILE,
]


def resolve_search_profile(topic: str, preferred_name: str = "auto") -> SearchProfile:
    normalized_preference = (preferred_name or "auto").strip().lower()
    if normalized_preference and normalized_preference != "auto":
        for profile in BUILTIN_SEARCH_PROFILES:
            if profile.name == normalized_preference:
                return profile

    normalized_topic = (topic or "").strip().lower()
    for profile in BUILTIN_SEARCH_PROFILES:
        if profile is GENERIC_PROFILE:
            continue
        for keyword in profile.match_keywords:
            if keyword.lower() in normalized_topic:
                return profile
    return GENERIC_PROFILE
