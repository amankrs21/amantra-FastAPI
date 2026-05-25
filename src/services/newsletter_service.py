from __future__ import annotations

from datetime import UTC, datetime, timedelta

import aiohttp
import orjson

from src.config import config
from src.helpers.response_helper import extract_domain
from src.repository.newsletter_repository import NewsletterRepository
from src.repository.watchlist_repository import WatchlistRepository

SEARCH_QUERIES = {
    "ai": "generative AI LLM ChatGPT Claude Gemini news today 2026",
    "quantum": "quantum computing technology breakthrough news today 2026",
    "tech": "technology news software startups innovations today 2026",
}

CACHE_HOURS = 45
CACHE_KEY = "newsletter_all"
MISTRAL_MODEL = "mistral-small-latest"


def _is_recent(published_date: str, max_hours: int = 72) -> bool:
    """Strictly check if an article was published within max_hours."""
    if not published_date:
        return False
    try:
        pd = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
        if pd.tzinfo is None:
            pd = pd.replace(tzinfo=UTC)
        cutoff = datetime.now(UTC) - timedelta(hours=max_hours)
        return pd > cutoff
    except Exception:
        return False


def _extract_year(published_date: str) -> int | None:
    """Extract year from a published date string."""
    if not published_date:
        return None
    try:
        pd = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
        return pd.year
    except Exception:
        return None


class NewsletterService:
    def __init__(self, newsletter_repo: NewsletterRepository, watchlist_repo: WatchlistRepository) -> None:
        self._cache_repo = newsletter_repo
        self._watchlist_repo = watchlist_repo

    async def get_feed(self, user_id: str, category: str | None = None) -> dict:
        cat = category or "all"
        now = datetime.now(UTC)

        if cat == "watchlist":
            return await self._fetch_watchlist_news(user_id, now)

        cached = await self._cache_repo.get_cache(CACHE_KEY)
        if cached:
            fetched_at = cached.get("fetchedAt")
            if fetched_at:
                if isinstance(fetched_at, str):
                    fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=UTC)
                if now - fetched_at < timedelta(hours=CACHE_HOURS):
                    articles = cached.get("articles", [])
                    if cat != "all":
                        articles = [a for a in articles if a.get("tag") == cat]
                    return {"articles": articles, "category": cat, "fetchedAt": cached["fetchedAt"], "cached": True}

        all_articles: list[dict] = []
        for key, query in SEARCH_QUERIES.items():
            articles = await self._search_and_summarize(query, key)
            all_articles.extend(articles)

        if all_articles:
            fetched_iso = now.isoformat()
            await self._cache_repo.set_cache(CACHE_KEY, {"articles": all_articles, "fetchedAt": fetched_iso})

        result = all_articles
        if cat != "all":
            result = [a for a in all_articles if a.get("tag") == cat]

        return {"articles": result, "category": cat, "fetchedAt": now.isoformat()}

    async def _fetch_watchlist_news(self, user_id: str, now: datetime) -> dict:
        cache_key = f"watchlist_news:{user_id}"

        cached = await self._cache_repo.get_cache(cache_key)
        if cached:
            fetched_at = cached.get("fetchedAt")
            if fetched_at:
                if isinstance(fetched_at, str):
                    fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=UTC)
                if now - fetched_at < timedelta(hours=CACHE_HOURS):
                    return {
                        "articles": cached.get("articles", []),
                        "category": "watchlist",
                        "fetchedAt": cached["fetchedAt"],
                        "cached": True,
                    }

        subscribed = await self._watchlist_repo.get_subscribed_by_user(user_id)
        titles = [item["title"] for item in subscribed]
        if not titles:
            return {"articles": [], "category": "watchlist", "message": "No subscribed items."}

        today = now.strftime("%Y-%m-%d")
        query = " OR ".join(f'"{t}" latest news {today}' for t in titles[:10])
        tavily_key = config.TAVILY_API_KEY
        if not tavily_key:
            return {"articles": [], "category": "watchlist", "message": "Tavily API key not configured."}

        raw_results = await self._tavily_search(tavily_key, query, max_results=15)
        if not raw_results:
            return {"articles": [], "category": "watchlist", "fetchedAt": now.isoformat()}

        # Strict date filtering — only keep articles from last 72 hours
        raw_results = [r for r in raw_results if _is_recent(r.get("published_date", ""), max_hours=72)]
        if not raw_results:
            return {"articles": [], "category": "watchlist", "fetchedAt": now.isoformat()}

        mistral_key = config.MISTRAL_API_KEY
        articles: list[dict] = []
        if mistral_key:
            articles = await self._mistral_curate_watchlist(raw_results, titles, mistral_key)

        if not articles:
            for r in raw_results:
                matched_title = next(
                    (t for t in titles if t.lower() in r["title"].lower() or t.lower() in r["content"].lower()), None
                )
                if matched_title:
                    articles.append(
                        {
                            "title": r["title"],
                            "description": r["content"][:200],
                            "url": r["url"],
                            "source": extract_domain(r["url"]),
                            "publishedAt": r.get("published_date", ""),
                            "watchlistTitle": matched_title,
                            "tag": "watchlist",
                            "imageUrl": "",
                        }
                    )

        fetched_iso = now.isoformat()
        await self._cache_repo.set_cache(cache_key, {"articles": articles, "fetchedAt": fetched_iso})
        return {"articles": articles, "category": "watchlist", "fetchedAt": fetched_iso}

    async def _tavily_search(self, api_key: str, query: str, max_results: int = 10) -> list[dict]:
        """Execute Tavily search with strict recency parameters."""
        raw_results: list[dict] = []
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "advanced",
                        "include_answer": False,
                        "days": 1,
                        "topic": "news",
                    },
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp,
            ):
                if resp.status == 200:
                    data = orjson.loads(await resp.read())
                    current_year = datetime.now(UTC).year
                    for r in data.get("results", [])[:max_results]:
                        pub_date = r.get("published_date", "")
                        # Hard reject anything not from current year
                        year = _extract_year(pub_date)
                        if year and year < current_year:
                            continue
                        raw_results.append(
                            {
                                "title": r.get("title", ""),
                                "content": r.get("content", ""),
                                "url": r.get("url", ""),
                                "score": r.get("score", 0),
                                "published_date": pub_date,
                            }
                        )
        except Exception as e:
            print(f"Tavily search error: {e}")
        return raw_results

    async def _search_and_summarize(self, query: str, tag: str) -> list[dict]:
        tavily_key = config.TAVILY_API_KEY
        if not tavily_key:
            return []

        raw_results = await self._tavily_search(tavily_key, query, max_results=10)

        # Strict: only keep articles with a published_date in last 72h
        recent_results = [r for r in raw_results if _is_recent(r.get("published_date", ""), max_hours=72)]

        # If we have recent results, use them; otherwise fall back to all (but LLM will filter)
        working_results = recent_results if recent_results else raw_results
        if not working_results:
            return []

        mistral_key = config.MISTRAL_API_KEY
        if mistral_key:
            curated = await self._mistral_curate(working_results, tag, mistral_key)
            if curated:
                return curated

        # Fallback: only use confirmed recent articles
        return [
            {
                "title": r["title"],
                "description": r["content"][:200],
                "url": r["url"],
                "source": extract_domain(r["url"]),
                "publishedAt": r.get("published_date", ""),
                "tag": tag,
                "imageUrl": "",
            }
            for r in recent_results[:6]
        ]

    async def _mistral_curate(self, results: list[dict], tag: str, api_key: str) -> list[dict]:
        results_text = "\n".join(
            f"{i + 1}. [{r['title']}]({r['url']})"
            f"{' (published: ' + r['published_date'] + ')' if r.get('published_date') else ' (NO DATE — REJECT THIS)'}"
            f"\n   {r['content'][:300]}"
            for i, r in enumerate(results)
        )
        now = datetime.now(UTC)
        now_str = now.strftime("%Y-%m-%d %H:%M UTC")
        current_year = now.year

        prompt = f"""You are a strict tech news curator. Current date/time: {now_str}.

CRITICAL RULES:
1. ONLY include articles published within the last 48 hours (after {(now - timedelta(hours=48)).strftime("%Y-%m-%d")})
2. REJECT any article from {current_year - 1} or earlier — these are OLD and STALE
3. REJECT articles without a published date
4. REJECT duplicates, clickbait, listicles, sponsored content, SEO spam
5. REJECT generic "what is X" explainer articles — only include ACTUAL NEWS with new information
6. Each article must contain genuinely NEW information (announcement, release, breakthrough, event)

Pick the top 4-6 most valuable and genuinely recent articles.

Return ONLY a JSON array (no markdown, no code fences):
[{{"title": "...", "summary": "one-line engaging summary of the actual news", "url": "...", "source": "domain.com", "publishedAt": "ISO date from the article"}}]

If NO articles pass the freshness/quality filter, return an empty array: []

Search results:
{results_text}"""

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": MISTRAL_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp,
            ):
                if resp.status == 200:
                    data = orjson.loads(await resp.read())
                    content = data["choices"][0]["message"]["content"].strip()
                    if content.startswith("```"):
                        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    curated = orjson.loads(content.strip().encode())
                    return [
                        {
                            "title": item.get("title", ""),
                            "description": item.get("summary", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", ""),
                            "publishedAt": item.get("publishedAt", ""),
                            "tag": tag,
                            "imageUrl": "",
                            "relevance": item.get("relevance", "high"),
                        }
                        for item in curated
                    ]
        except Exception as e:
            print(f"Mistral curation error: {e}")
        return []

    async def _mistral_curate_watchlist(self, results: list[dict], titles: list[str], api_key: str) -> list[dict]:
        results_text = "\n".join(
            f"{i + 1}. [{r['title']}]({r['url']})"
            f"{' (published: ' + r['published_date'] + ')' if r.get('published_date') else ' (NO DATE — REJECT)'}"
            f"\n   {r['content'][:300]}"
            for i, r in enumerate(results)
        )
        titles_text = ", ".join(f'"{t}"' for t in titles)
        now = datetime.now(UTC)
        now_str = now.strftime("%Y-%m-%d %H:%M UTC")
        current_year = now.year

        prompt = f"""You are a strict entertainment news curator. Current date/time: {now_str}.
The user subscribes to: {titles_text}

CRITICAL RULES:
1. ONLY articles from the last 48 hours (after {(now - timedelta(hours=48)).strftime("%Y-%m-%d")})
2. REJECT anything from {current_year - 1} or earlier
3. REJECT articles without dates
4. For movies/TV: ONLY include concrete news (release dates, trailers, casting, renewals, streaming dates)
5. REJECT: reviews, recaps, fan theories, "best of" lists, old news rehashed
6. MAX 1-2 articles per title. If nothing genuinely new exists for a title, return NOTHING for it.

Return ONLY a JSON array:
[{{"title": "...", "summary": "...", "url": "...", "source": "domain.com", "watchlistTitle": "exact match from user list", "publishedAt": "ISO date"}}]

If nothing passes filters, return: []

Search results:
{results_text}"""

        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": MISTRAL_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 3000,
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp,
            ):
                if resp.status == 200:
                    data = orjson.loads(await resp.read())
                    content = data["choices"][0]["message"]["content"].strip()
                    if content.startswith("```"):
                        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    curated = orjson.loads(content.strip().encode())
                    return [
                        {
                            "title": item.get("title", ""),
                            "description": item.get("summary", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", ""),
                            "publishedAt": item.get("publishedAt", ""),
                            "watchlistTitle": item.get("watchlistTitle", ""),
                            "tag": "watchlist",
                            "imageUrl": "",
                        }
                        for item in curated
                    ]
        except Exception as e:
            print(f"Mistral watchlist curation error: {e}")
        return []
