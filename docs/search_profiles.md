# Search Profiles

## Goal

Keep domain-specific Tavily search strategy separate from the generic report pipeline.

## Current Design

- Generic Tavily request building stays in `app/backend/tavily_connector.py`
- Public-mainland official source aggregation lives in `app/backend/official_sources.py`
- Domain matching and search strategy live in `app/backend/search_profiles.py`
- Global overrides still come from `app/backend/settings.py`

## How It Works

1. The user submits a topic.
2. `query_intent.py` normalizes the topic and infers search intent.
3. `security_identifier.py` standardizes equity-style identifiers into canonical symbols such as `US:TSLA`, `SHSE:600519`, `HKEX:0700`.
4. `TavilyConnector` resolves a search profile.
5. `OfficialPublicSourceConnector` decides which mainland-official sources are relevant to the intent.
6. The profile contributes:
   - query hint
   - Tavily topic
   - include domains
   - exclude domains
7. Environment variables can still override shared behavior such as:
   - `ENABLE_OFFICIAL_SOURCES`
   - `OFFICIAL_SOURCE_NAMES`
   - `SEARCH_PROFILE`
   - `TAVILY_SEARCH_DEPTH`
   - `TAVILY_INCLUDE_RAW_CONTENT`
   - `TAVILY_INCLUDE_DOMAINS`
   - `TAVILY_EXCLUDE_DOMAINS`

## Mainland Official Sources

Phase 1 of the mainland data foundation adds these free public sources:

- `cninfo`
  - CNINFO home/latest disclosure feed for public company announcements
- `stats`
  - National Bureau of Statistics RSS feeds for releases and interpretations
- `csrc`
  - China Securities Regulatory Commission public regulation/news lists
- `sse`
  - Shanghai Stock Exchange public news and conference pages
- `szse`
  - Shenzhen Stock Exchange public news and disclosure pages
- `miit`
  - Ministry of Industry and Information Technology public site updates
- `safe`
  - State Administration of Foreign Exchange public macro/statistics lists
- `customs`
  - General Administration of Customs public trade/statistics pages
- `bse`
  - Beijing Stock Exchange public news and disclosure pages

The official-source layer is designed as an additive source backend:

- official public sources appear first in the local chain when matched
- Tavily still supplements breadth and non-official context
- each source adapter fails independently, so a single source outage does not block report generation

## Current Profiles

- `generic-industry`
  - default fallback for most topics
- `shipping-finance-leasing`
  - tuned for maritime finance and vessel leasing topics
- `macro-rates-commodities`
  - tuned for macro, rates, FX, and commodity investor queries
- `stock-industry-news`
  - tuned for equity investors tracking sector and industry developments
- `ticker-company-news`
  - tuned for single-stock and listed-company event tracking
- `earnings-and-guidance`
  - tuned for earnings releases, guidance changes, and estimate revisions

## Adding a New Domain

Add one new `SearchProfile` in `app/backend/search_profiles.py` with:

- `name`
- `description`
- `match_keywords`
- `query_hint`
- `include_domains`
- `exclude_domains`

Then add it to `BUILTIN_SEARCH_PROFILES`.

No changes are required in:

- `tavily_connector.py`
- `live_report_service_v2.py`
- `mvp_main_v3.py`

For a new official source, add one adapter definition in `app/backend/official_sources.py` and keep the report pipeline unchanged.

## Security Identifier Layer

`security_identifier.py` currently provides lightweight normalization for:

- US tickers: `TSLA` -> `US:TSLA`
- A-share codes: `600519` -> `SHSE:600519`
- Hong Kong symbols: `0700.HK` -> `HKEX:0700`

This layer is intentionally lightweight and local-first.
It can later be extended with external mapping providers such as:

- OpenFIGI
- SEC CIK mapping
- exchange symbol master files

## Recommended Expansion Path

- semiconductor
- new energy / battery
- AI / model ecosystem
- medical devices
- automotive supply chain
- macro / rates / commodities
