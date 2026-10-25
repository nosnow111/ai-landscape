import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

QUERIES = {
    "code_tools": [
        "most popular AI code generation tools developer adoption 2026",
        "GitHub Copilot vs Cursor vs Claude Code usage statistics 2026",
        "AI coding tools complete list 2026 alternatives lesser known",
        "best AI IDE plugins extensions developer tools 2026",
    ],
    "models": [
        "most used large language models developers 2026 survey rankings",
        "GPT-4 Claude Gemini Llama DeepSeek usage statistics market share 2026",
        "top LLM API adoption leaderboard 2026",
        "emerging new LLM models 2026 rising adoption alternatives GPT",
        "open source large language models top adoption 2026",
    ],
    "repositories": [
        "Hugging Face model downloads statistics 2026",
        "top AI model repositories platforms adoption 2026",
        "AI model hosting platforms alternatives Hugging Face complete list 2026",
    ],
    "enterprise_apis": [
        "AWS Bedrock vs Azure OpenAI vs Google Vertex AI enterprise adoption 2026",
        "enterprise AI model API aggregators comparison 2026",
        "Snowflake Cortex IBM watsonx enterprise AI platform adoption 2026",
        "why enterprises use cloud AI aggregators instead of direct APIs 2026",
    ],
    "ml_platforms": [
        "AWS SageMaker vs Google Vertex AI vs Azure ML adoption 2026",
        "top MLOps platforms enterprise adoption 2026",
        "Databricks vs SageMaker ML platform comparison 2026",
        "ML training deployment platforms complete list 2026",
    ],
    "databases": [
        "AI features databases Snowflake BigQuery PostgreSQL pgvector 2026",
        "vector database adoption enterprise AI 2026",
        "vector databases complete list alternatives pgvector Pinecone Weaviate 2026",
    ],
    "observability": [
        "LLM observability monitoring tools adoption 2026",
        "AI cost monitoring LangSmith Helicone usage 2026",
        "LLM monitoring tools complete list alternatives 2026",
    ],
    "image_gen": [
        "most popular AI image generation tools users 2026 rankings",
        "Midjourney vs DALL-E vs Stable Diffusion vs Flux adoption 2026",
        "AI image generation tools complete directory list 2026 lesser known",
    ],
    "video_gen": [
        "most popular AI video generation tools 2026 adoption",
        "Sora Runway Pika Kling Luma video AI comparison 2026",
        "AI video generation tools emerging new 2026 complete list",
    ],
    "llm_optimization": [
        "LLM cost optimization techniques reduce token usage 2026",
        "prompt caching semantic caching LLM API cost reduction 2026",
        "LLM inference optimization batching right-sizing quantization 2026",
        "reduce OpenAI Anthropic API costs best practices 2026",
    ],
    "fine_tuning": [
        "LLM fine-tuning platforms tools adoption 2026 developer survey",
        "OpenAI fine-tuning vs Hugging Face AutoTrain vs Together AI comparison 2026",
        "fine-tuning vs RAG vs prompt engineering when to use 2026",
        "open source LLM fine-tuning tools Axolotl Unsloth LLaMA-Factory 2026",
    ],
    "web_scrapers": [
        "top AI web scraping browser automation tools developers 2026",
        "Firecrawl Apify AgentQL Browserbase adoption 2026",
        "AI web scraping tools complete directory alternatives 2026",
    ],
    "workspace": [
        "most popular AI productivity workspace tools 2026 adoption",
        "NotebookLM Gemini Notebook Microsoft Copilot M365 Notion AI usage 2026",
        "AI meeting recorder note taker Otter Fireflies Wave Fathom adoption 2026",
        "AI productivity tools complete directory list 2026 lesser known",
        "AI meeting tools alternatives complete list 2026",
        "Devin Cognition AI Windsurf coding agent 2026",
        "OpenAI Codex agentic coding agent 2026 adoption",
    ],
}


def _search_with_retry(query: str, retries: int = 3) -> dict:
    """Tavily search with exponential backoff on 429/432 rate limit errors."""
    import time
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
            if ("429" in msg or "432" in msg) and attempt < retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"  Rate limited — retrying '{query[:50]}...' in {wait}s")
                time.sleep(wait)
            else:
                raise
    return {}


def research_section(key: str) -> tuple[str, list[str]]:
    """Returns (context_text, list_of_source_urls)"""
    import time
    queries = QUERIES.get(key, [])
    results = []
    sources = []
    for i, query in enumerate(queries):
        if i > 0:
            time.sleep(0.3)  # small gap between queries within a section
        try:
            response = _search_with_retry(query)
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
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    keys = list(QUERIES.keys())

    def _research(args):
        key, stagger = args
        if stagger > 0:
            time.sleep(stagger * 0.5)  # stagger section starts by 0.5s each
        print(f"  Researching: {key}")
        context, sources = research_section(key)
        return key, {"context": context, "sources": sources}

    # Cap concurrent sections at 6 to stay within Tavily rate limits
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
