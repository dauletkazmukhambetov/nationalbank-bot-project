from __future__ import annotations

import aiohttp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def normalize_year_url(url: str, year: int) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["date_from"] = [f"{year}-01-01"]
    query["date_to"] = [f"{year}-12-31"]
    if "lang" not in query:
        query["lang"] = ["ru"]
    new_query = urlencode(query, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


async def fetch_json(url: str, year: int) -> object:
    final_url = normalize_year_url(url, year)
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {"User-Agent": "TengenomikaBot/1.0"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(final_url) as response:
            response.raise_for_status()
            try:
                return await response.json(content_type=None)
            except Exception:
                text = await response.text()
                return {"raw_response": text, "requested_url": final_url}
