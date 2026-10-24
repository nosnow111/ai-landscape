import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

QUERIES = {
    "code_tools": [
        "most popular AI code generation tools developer adoption 2026",
        "GitHub Copilot vs Cursor vs Claude Code usage statistics 2026",
    ],
    "models": [
        "most used large language models developers 2026 survey rankings",
        "GPT-4 Claude Gemini Llama DeepSeek usage statistics market share 2026",
        "top LLM API adoption leaderboard 2026",
    ],
    "repositories": [
        "Hugging Face model downloads statistics 2026",
        "top AI model repositories platforms adoption 2026",
    ],
    "databases": [
        "AI features databases Snowflake BigQuery PostgreSQL pgvector 2026",
        "vector database adoption enterprise AI 2026",
    ],
    "observability": [
        "LLM observability monitoring tools adoption 2026",
        "AI cost monitoring LangSmith Helicone usage 2026",
    ],
}


def research_section(key: str) -> str:
    queries = QUERIES.get(key, [])
    results = []
    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True,
            )
            if response.get("answer"):
                results.append(f"Q: {query}\nA: {response['answer']}")
            for r in response.get("results", []):
                snippet = r.get("content", "")[:400]
                if snippet:
                    results.append(f"Source ({r.get('url', '')}): {snippet}")
        except Exception as e:
            print(f"  Search error for '{query}': {e}")
    return "\n\n".join(results)


def research_all() -> dict:
    data = {}
    for key in QUERIES:
        print(f"  Researching: {key}")
        data[key] = research_section(key)
    return data


if __name__ == "__main__":
    results = research_all()
    for k, v in results.items():
        print(f"\n=== {k} ===\n{v[:300]}...")
