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


BUILTIN_SEARCH_PROFILES = [
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
