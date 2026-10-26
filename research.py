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
from dotenv import load_dotenv

load_dotenv()

# 2 queries per section = 26/run × 30 days = ~780/month
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

def _tavily_search(query: str, retries: int = 3) -> dict | None:
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
            return client.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True,
            )
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

def _search(query: str) -> dict:
    """Try Firecrawl → Tavily → Serper; return empty dict if all fail."""
    for fn in (_firecrawl_search, _tavily_search, _serper_search):
        result = fn(query)
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
    results = []
    sources = []
    for i, query in enumerate(queries):
        if i > 0:
            time.sleep(0.3)
        try:
            response = _search(query)
            if response.get("answer"):
                results.append(f"Q: {query}\nA: {response['answer']}")
            for r in response.get("results", []):
                url = r.get("url", "")
                snippet = r.get("content", "")[:400]
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
