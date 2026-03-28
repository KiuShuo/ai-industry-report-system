# Search Profiles

## Goal

Keep domain-specific Tavily search strategy separate from the generic report pipeline.

## Current Design

- Generic Tavily request building stays in `app/backend/tavily_connector.py`
- Domain matching and search strategy live in `app/backend/search_profiles.py`
- Global overrides still come from `app/backend/settings.py`

## How It Works

1. The user submits a topic.
2. `TavilyConnector` resolves a search profile.
3. The profile contributes:
   - query hint
   - Tavily topic
   - include domains
   - exclude domains
4. Environment variables can still override shared behavior such as:
   - `SEARCH_PROFILE`
   - `TAVILY_SEARCH_DEPTH`
   - `TAVILY_INCLUDE_RAW_CONTENT`
   - `TAVILY_INCLUDE_DOMAINS`
   - `TAVILY_EXCLUDE_DOMAINS`

## Current Profiles

- `generic-industry`
  - default fallback for most topics
- `shipping-finance-leasing`
  - tuned for maritime finance and vessel leasing topics

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

## Recommended Expansion Path

- semiconductor
- new energy / battery
- AI / model ecosystem
- medical devices
- automotive supply chain
