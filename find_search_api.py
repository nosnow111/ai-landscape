"""
One-time utility: research current web search API options and recommend the best one.

Uses Serper to find what's available in 2026, then asks Claude to analyze
and recommend based on free tier, pricing, quality, and ease of integration.

Usage:
  python find_search_api.py
"""

import json
import os
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()

QUERIES = [
    "best web search API developers 2026 free tier",
    "Tavily alternatives web search API 2026 comparison",
    "Serper vs Tavily vs Exa vs Brave search API 2026",
    "new web search API 2026 developer affordable",
]


def search(query: str) -> list[dict]:
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        print("SERPER_API_KEY not set")
        return []
    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        json={"q": query, "num": 5},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("organic", [])


def gather_research() -> str:
    print("Searching for current web search API options...\n")
    snippets = []
    for query in QUERIES:
        print(f"  {query}")
        results = search(query)
        for r in results[:3]:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            link = r.get("link", "")
            if snippet:
                snippets.append(f"[{title}] ({link})\n{snippet}")
    return "\n\n".join(snippets)


def analyze(research: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    prompt = f"""You are evaluating web search APIs for a small developer project that runs ~26 search queries per day (~780/month).

Requirements:
- Needs a free tier covering at least 800 queries/month OR very cheap pay-as-you-go
- Returns useful snippets/content for AI research grounding (not just URLs)
- Simple REST API, easy to integrate in Python
- Reliable uptime

Current setup: Tavily (primary, 1,000 free/month) + Serper (fallback, 2,500 one-time free credits)

Here is live research about what's available in 2026:

{research}

Based on this research, provide:
1. A ranked list of the top 3-4 best options with free tier details and pricing
2. A clear recommendation for what to use as primary vs fallback
3. Any new options not currently in our setup that are worth switching to

Be specific about free tier limits and pricing. Flag anything that launched or significantly changed after mid-2025."""

    for model in ("claude-haiku-4-5-20251001", "claude-sonnet-4-6"):
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            print(f"(analyzed with {model})\n")
            return msg.content[0].text.strip()
        except Exception as e:
            print(f"  {model} failed: {e}")
    return "(Claude unavailable — read raw research above)"


if __name__ == "__main__":
    research = gather_research()

    print("\n" + "=" * 60)
    print("RAW RESEARCH")
    print("=" * 60)
    print(research)

    print("\n" + "=" * 60)
    print("CLAUDE ANALYSIS")
    print("=" * 60)
    recommendation = analyze(research)
    print(recommendation)
    print("=" * 60)
