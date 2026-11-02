"""
Web research for content generation.

Provider priority:
  1. Firecrawl — AI-optimized search + content extraction; uses FIRECRAWL_API_KEY
  2. Tavily    — best answer synthesis; uses TAVILY_API_KEY
  3. Serper    — Google results fallback; uses SERPER_API_KEY
  4. None      — skips research; Claude generates from training data only

Set whichever key(s) you have in .env. Firecrawl is tried first (1,000 free/month),
then Tavily, then Serper. All three give the same 1,000 free queries/month or better.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Current month/year injected into time-sensitive queries at module load
_THIS_MONTH = datetime.now().strftime("%B %Y")   # e.g. "October 2026"
_THIS_WEEK  = datetime.now().strftime("%Y-%m-%d") # e.g. "2026-10-30"

# Vendor blog domains + major news outlets — for extended vendor-announcement query
_VENDOR_DOMAINS_EARLY = [
    "anthropic.com", "openai.com", "deepmind.google", "blog.google",
    "ai.meta.com", "blogs.microsoft.com", "mistral.ai", "x.ai",
    "huggingface.co", "stability.ai", "groq.com", "cohere.com",
    "reuters.com", "apnews.com", "techcrunch.com", "theverge.com",
    "wired.com", "arstechnica.com", "venturebeat.com", "fortune.com",
    "bloomberg.com", "wsj.com", "cnbc.com", "nytimes.com",
]

# Vendor blogs only — direct pull for announcements not yet covered by news outlets
_VENDOR_BLOGS_ONLY = [
    "anthropic.com", "openai.com", "deepmind.google", "blog.google",
    "ai.meta.com", "blogs.microsoft.com", "mistral.ai", "x.ai",
    "huggingface.co", "cohere.com", "groq.com", "stability.ai",
    "aws.amazon.com", "azure.microsoft.com", "cloud.google.com",
]

# 2-3 queries per section; ai_news gets 3 = ~28/run × 30 days = ~840/month
QUERIES = {
    "code_tools": [
        "most popular AI code generation tools developer adoption 2026",
        "GitHub Copilot vs Cursor vs Claude Code usage statistics 2026",
    ],
    "models": [
        "most used large language models developers 2026 currently available not retired",
        "GPT-5 Claude Gemini Llama DeepSeek current models available API 2026 latest versions",
    ],
    "repositories": [
        "Hugging Face model downloads statistics 2026",
        "top AI model repositories platforms adoption 2026",
    ],
    "enterprise_apis": [
        "AWS Bedrock vs Azure OpenAI vs Google Vertex AI enterprise adoption 2026",
        "Snowflake Cortex IBM watsonx enterprise AI platform adoption 2026",
    ],
    "ml_platforms": [
        "AWS SageMaker vs Google Vertex AI vs Azure ML adoption 2026",
        "Databricks vs SageMaker ML platform comparison 2026",
    ],
    "databases": [
        "AI features databases Snowflake BigQuery PostgreSQL pgvector 2026",
        "vector database adoption enterprise AI 2026",
    ],
    "observability": [
        "LLM observability monitoring tools adoption 2026",
        "AI cost monitoring LangSmith Helicone usage 2026",
    ],
    "image_gen": [
        "most popular AI image generation tools users 2026 rankings",
        "Midjourney vs DALL-E vs Stable Diffusion vs Flux adoption 2026",
    ],
    "video_gen": [
        "most popular AI video generation tools 2026 adoption",
        "Sora Runway Pika Kling Luma video AI comparison 2026",
    ],
    "llm_optimization": [
        "LLM cost optimization techniques reduce token usage 2026",
        "prompt caching semantic caching LLM API cost reduction 2026",
    ],
    "fine_tuning": [
        "LLM fine-tuning platforms tools adoption 2026 developer survey",
        "OpenAI fine-tuning vs Hugging Face AutoTrain vs Together AI comparison 2026",
    ],
    "mcp_tools": [
        "most popular MCP servers aggregators developer adoption 2026",
        "Composio Smithery agentgateway Playwright MCP GitHub MCP usage statistics 2026",
    ],
    "web_scrapers": [
        "top AI web scraping browser automation tools developers 2026",
        "Firecrawl Apify AgentQL Browserbase adoption 2026",
    ],
    "workspace": [
        "most popular AI productivity workspace tools 2026 adoption",
        "NotebookLM Gemini Notebook Microsoft Copilot M365 Notion AI usage 2026",
    ],
    "ai_news": [
        f"AI news today {_THIS_WEEK} breaking announcements",
        f"AI news yesterday latest {_THIS_MONTH}",
        f"Anthropic OpenAI Google Meta Microsoft AI release announcement {_THIS_WEEK}",
        f"AI funding regulation enterprise deal {_THIS_WEEK}",
        # vendor query via news outlets: 30-day window
        (f"Anthropic OpenAI Google Meta Microsoft xAI model launch product release update {_THIS_MONTH}", 30, _VENDOR_DOMAINS_EARLY),
        # direct pull from vendor blogs only — bypasses news outlet coverage gaps
        (f"new model release product update announcement {_THIS_MONTH}", 30, _VENDOR_BLOGS_ONLY),
    ],
    "emerging_trends": [
        "emerging AI trends 2026 gaining momentum",
        "AI reasoning models agents inference compute multimodal trends 2026",
    ],
    "model_pricing": [
        f"GPT-4o Claude Gemini API pricing per million tokens {_THIS_MONTH}",
        f"LLM API cost comparison input output tokens 2026 {_THIS_MONTH}",
    ],
}


# ── Firecrawl ──────────────────────────────────────────────────────────────

def _firecrawl_search(query: str, retries: int = 3) -> dict | None:
    """Returns normalized response dict (Tavily-like shape), or None."""
    key = os.environ.get("FIRECRAWL_API_KEY")
    if not key:
        return None
    import requests as _requests
    for attempt in range(retries):
        try:
            resp = _requests.post(
                "https://api.firecrawl.dev/v1/search",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"query": query, "limit": 5},
                timeout=15,
            )
            if resp.status_code == 429:
                wait = 2 ** attempt
                print(f"  Firecrawl rate limited — retrying in {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("data", [])[:3]:
                results.append({
                    "url": item.get("url", ""),
                    "content": item.get("description") or item.get("markdown", "")[:400],
                })
            return {"answer": "", "results": results}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  Firecrawl error for '{query[:50]}': {e}")
                return None
    return None


# ── Tavily ─────────────────────────────────────────────────────────────────

# Trusted domains for AI news — Tavily restricts its news search to these only.
_NEWS_DOMAINS = [
    "reuters.com", "apnews.com", "techcrunch.com", "theverge.com",
    "wired.com", "arstechnica.com", "technologyreview.com", "venturebeat.com",
    "fortune.com", "forbes.com", "cnbc.com", "marketwatch.com",
    "bbc.com", "bbc.co.uk", "theguardian.com", "bloomberg.com",
    "wsj.com", "ft.com", "nytimes.com", "businessinsider.com",
    "washingtonpost.com", "economist.com", "nature.com", "science.org",
    "axios.com", "theatlantic.com", "fastcompany.com",
]



def _tavily_search(query: str, retries: int = 3, news_mode: bool = False, days: int = 14,
                   domains_override: list | None = None) -> dict | None:
    """Returns Tavily response dict, or None if unavailable/rate-limited."""
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        return None
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=key)
    except ImportError:
        return None

    for attempt in range(retries):
        try:
            kwargs = dict(
                query=query,
                search_depth="advanced" if news_mode else "basic",
                max_results=3,
                include_answer=True,
            )
            if news_mode:
                kwargs["topic"] = "news"
                kwargs["days"] = days
                kwargs["max_results"] = 10
                kwargs["include_domains"] = domains_override if domains_override is not None else _NEWS_DOMAINS
            return client.search(**kwargs)
        except Exception as e:
            msg = str(e)
            if ("429" in msg or "432" in msg or "quota" in msg.lower()) and attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  Tavily rate limited — retrying in {wait}s")
                time.sleep(wait)
            else:
                return None
    return None


# ── Serper ─────────────────────────────────────────────────────────────────

def _serper_search(query: str) -> dict | None:
    """Returns normalized response dict (Tavily-like shape), or None."""
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        return None
    try:
        import requests
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": 5},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("organic", [])[:3]:
            results.append({
                "url": item.get("link", ""),
                "content": item.get("snippet", ""),
            })
        answer = data.get("answerBox", {}).get("answer") or data.get("answerBox", {}).get("snippet", "")
        return {"answer": answer, "results": results}
    except Exception as e:
        print(f"  Serper error for '{query[:50]}': {e}")
        return None


# ── unified search ─────────────────────────────────────────────────────────

def _search(query: str, news_mode: bool = False, days: int = 14,
            domains_override: list | None = None) -> dict:
    """Try providers in order; for news_mode skip Firecrawl and Serper (no recency filter on either)."""
    if not news_mode:
        result = _firecrawl_search(query)
        if result is not None:
            return result
    result = _tavily_search(query, news_mode=news_mode, days=days,
                            domains_override=domains_override)
    if result is not None:
        return result
    if not news_mode:
        result = _serper_search(query)
        if result is not None:
            return result
    return {}


def _active_provider() -> str:
    if os.environ.get("FIRECRAWL_API_KEY"):
        return "Firecrawl"
    if os.environ.get("TAVILY_API_KEY"):
        return "Tavily"
    if os.environ.get("SERPER_API_KEY"):
        return "Serper"
    return "none"


# ── section research ───────────────────────────────────────────────────────

def research_section(key: str) -> tuple[str, list[str]]:
    """Returns (context_text, list_of_source_urls)"""
    queries = QUERIES.get(key, [])
    news_mode = (key == "ai_news")
    results = []
    sources = []
    for i, query in enumerate(queries):
        if i > 0:
            time.sleep(0.3)
        # support (query, days) or (query, days, domains) tuples
        days_override = 14
        domains_override = None
        if isinstance(query, tuple):
            query, days_override, *rest = query
            domains_override = rest[0] if rest else None
        try:
            response = _search(query, news_mode=news_mode, days=days_override,
                               domains_override=domains_override)
            if response.get("answer"):
                results.append(f"Q: {query}\nA: {response['answer']}")
            for r in response.get("results", []):
                url = r.get("url", "")
                snippet = r.get("content", "")[:600]
                if snippet:
                    results.append(f"Source ({url}): {snippet}")
                if url and url not in sources:
                    sources.append(url)
        except Exception as e:
            print(f"  Search error for '{query}': {e}")
    return "\n\n".join(results), sources


def research_all() -> dict:
    """Returns dict of key -> {'context': str, 'sources': list}"""
    provider = _active_provider()
    if provider == "none":
        print("  No search API key found — skipping web research.")
        return {}

    print(f"  Search provider: {provider}")
    keys = list(QUERIES.keys())

    def _research(args):
        key, stagger = args
        if stagger > 0:
            time.sleep(stagger * 0.5)
        print(f"  Researching: {key}")
        context, sources = research_section(key)
        return key, {"context": context, "sources": sources}

    data = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_research, (key, i)): key
            for i, key in enumerate(keys)
        }
        for future in as_completed(futures):
            key, result = future.result()
            data[key] = result
    return data


if __name__ == "__main__":
    results = research_all()
    for k, v in results.items():
        print(f"\n=== {k} ===\n{v['context'][:300]}...")
        print(f"Sources: {v['sources']}")
