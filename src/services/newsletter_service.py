from __future__ import annotations

from datetime import UTC, datetime, timedelta

import aiohttp
import orjson

from src.config import config
from src.helpers.response_helper import extract_domain
from src.repository.newsletter_repository import NewsletterRepository
from src.repository.watchlist_repository import WatchlistRepository

SEARCH_QUERIES = {
    "ai": "latest generative AI news LLM ChatGPT Claude Gemini",
    "quantum": "quantum computing technology breakthrough news",
    "tech": "latest technology news software startups innovations",
}

CACHE_HOURS = 48
CACHE_KEY = "newsletter_all"
MISTRAL_MODEL = "mistral-small-latest"


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

        query = " OR ".join(f'"{t}" latest news' for t in titles[:20])
        tavily_key = config.TAVILY_API_KEY
        if not tavily_key:
            return {"articles": [], "category": "watchlist", "message": "Tavily API key not configured."}

        raw_results: list[dict] = []
        try:
            async with aiohttp.ClientSession() as session, session.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "max_results": 20,
                    "search_depth": "basic",
                    "include_answer": False,
                    "days": 2,
                },
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 200:
                    data = orjson.loads(await resp.read())
                    for r in data.get("results", [])[:20]:
                        raw_results.append(
                            {
                                "title": r.get("title", ""),
                                "content": r.get("content", ""),
                                "url": r.get("url", ""),
                                "published_date": r.get("published_date", ""),
                            }
                        )
        except Exception as e:
            print(f"Tavily watchlist search error: {e}")
            return {"articles": [], "category": "watchlist"}

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
                            "watchlistTitle": matched_title,
                            "tag": "watchlist",
                            "imageUrl": "",
                        }
                    )

        fetched_iso = now.isoformat()
        await self._cache_repo.set_cache(cache_key, {"articles": articles, "fetchedAt": fetched_iso})
        return {"articles": articles, "category": "watchlist", "fetchedAt": fetched_iso}

    async def _mistral_curate_watchlist(self, results: list[dict], titles: list[str], api_key: str) -> list[dict]:
        results_text = "\n".join(
            f"{i + 1}. [{r['title']}]({r['url']}){' (published: ' + r['published_date'] + ')' if r.get('published_date') else ''}\n   {r['content'][:200]}"
            for i, r in enumerate(results)
        )
        titles_text = ", ".join(f'"{t}"' for t in titles)
        now_str = datetime.now(UTC).strftime("%Y-%m-%d")

        prompt = f"""You are a news curator. Today is {now_str}. The user subscribes to news about these titles: {titles_text}

From these search results, pick MAX 1-2 most relevant news articles PER title. Only include articles from the LAST 48 HOURS.

IMPORTANT: For movies/TV series, ONLY include articles that contain concrete information about:
- New release dates or premiere dates
- Trailer drops or official announcements
- Streaming availability dates
Do NOT include generic reviews, fan theories, old recaps, or articles without specific release/date information.

Return ONLY a JSON array (no markdown, no code fences):
[{{"title": "...", "summary": "...", "url": "...", "source": "domain.com", "watchlistTitle": "matched title from list"}}]

If no articles have relevant new release/date information for a title, return nothing for that title.

Search results:
{results_text}

Rules:
- MAX 1-2 articles per watchlist title
- Skip titles with no relevant recent news (return nothing for them)
- watchlistTitle must exactly match one of: {titles_text}
- Summary: 1-2 engaging sentences
- ONLY last 48h articles
- Valid JSON only"""

        try:
            async with aiohttp.ClientSession() as session, session.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": MISTRAL_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 3000,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
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
                            "watchlistTitle": item.get("watchlistTitle", ""),
                            "tag": "watchlist",
                            "imageUrl": "",
                        }
                        for item in curated
                    ]
        except Exception as e:
            print(f"Mistral watchlist curation error: {e}")
        return []

    async def _search_and_summarize(self, query: str, tag: str) -> list[dict]:
        tavily_key = config.TAVILY_API_KEY
        if not tavily_key:
            return []

        raw_results: list[dict] = []
        try:
            async with aiohttp.ClientSession() as session, session.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "max_results": 10,
                    "search_depth": "basic",
                    "include_answer": False,
                    "days": 2,
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    data = orjson.loads(await resp.read())
                    for r in data.get("results", [])[:10]:
                        raw_results.append(
                            {
                                "title": r.get("title", ""),
                                "content": r.get("content", ""),
                                "url": r.get("url", ""),
                                "score": r.get("score", 0),
                                "published_date": r.get("published_date", ""),
                            }
                        )
        except Exception as e:
            print(f"Tavily search error: {e}")
            return []

        if not raw_results:
            return []

        cutoff = datetime.now(UTC) - timedelta(hours=48)
        filtered_results: list[dict] = []
        for r in raw_results:
            pd = r.get("published_date", "")
            if pd:
                try:
                    pub_dt = datetime.fromisoformat(pd.replace("Z", "+00:00"))
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=UTC)
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass
            filtered_results.append(r)
        raw_results = filtered_results
        if not raw_results:
            return []

        mistral_key = config.MISTRAL_API_KEY
        if mistral_key:
            curated = await self._mistral_curate(raw_results, tag, mistral_key)
            if curated:
                return curated

        return [
            {
                "title": r["title"],
                "description": r["content"][:200],
                "url": r["url"],
                "source": extract_domain(r["url"]),
                "publishedAt": "",
                "tag": tag,
                "imageUrl": "",
            }
            for r in raw_results[:8]
        ]

    async def _mistral_curate(self, results: list[dict], tag: str, api_key: str) -> list[dict]:
        results_text = "\n".join(
            f"{i + 1}. [{r['title']}]({r['url']}){' (published: ' + r['published_date'] + ')' if r.get('published_date') else ''}\n   {r['content'][:200]}"
            for i, r in enumerate(results)
        )
        now_str = datetime.now(UTC).strftime("%Y-%m-%d")

        prompt = f"""You are a tech news curator. Today is {now_str}. From these search results, pick the top 6-8 most interesting and relevant articles that were published within the LAST 48 HOURS ONLY. Discard any article that appears to be older than 2 days.

Return ONLY a JSON array (no markdown, no code fences) with objects like:
[{{"title": "...", "summary": "...", "url": "...", "source": "domain.com", "relevance": "high/medium"}}]

Search results:
{results_text}

Rules:
- ONLY include articles from the last 48 hours — reject anything older
- Skip duplicates, low-quality, or irrelevant results
- Summary should be informative and engaging (1-2 sentences)
- Source is just the domain name
- Return valid JSON only"""

        try:
            async with aiohttp.ClientSession() as session, session.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": MISTRAL_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
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
                            "publishedAt": "",
                            "tag": tag,
                            "imageUrl": "",
                            "relevance": item.get("relevance", "medium"),
                        }
                        for item in curated
                    ]
        except Exception as e:
            print(f"Mistral curation error: {e}")
        return []
