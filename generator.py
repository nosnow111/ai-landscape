import os
import json
import anthropic
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SECTIONS = {
    "code_tools": {
        "title": "Code Generation Tools",
        "prompt": (
            "List the TOP 10 AI code generation tools ranked by actual developer adoption and usage "
            "as of your knowledge cutoff. Be completely objective — base rankings on developer surveys "
            "(Stack Overflow, JetBrains), download stats, and public adoption data. Include whichever "
            "tools actually belong in the top 10; do not force any specific tool into the list. "
            "For each tool cover: vendor, pricing (free tier + paid), key strengths, IDE support, "
            "best use case, and vendor website URL. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the AI code generation landscape) and "
            "'tools' (array of up to 10 items SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "strengths (list of strings), ide_support (list), best_for (string), url (string))."
        ),
    },
    "models": {
        "title": "Major AI Models",
        "prompt": (
            "List the TOP 10 large language models ranked strictly by real-world developer usage and adoption "
            "as of your knowledge cutoff. Be completely objective and unbiased — do NOT assume any model belongs "
            "in the list. Base rankings on: API call volume, developer surveys (Stack Overflow, JetBrains), "
            "HuggingFace download stats, and public adoption data. Include whichever models actually belong "
            "in the top 10 by usage — if GPT-4o, Gemini, Llama, DeepSeek, Claude, Mistral, Grok or others "
            "qualify, include them; if they do not, omit them. "
            "For each model provide: name, vendor, context window, input/output cost per 1M tokens, "
            "open source flag, usage rank (integer 1=most used), popularity_notes (1 sentence citing the "
            "specific data or reason for this rank), key strengths (list), best use case, vendor website URL. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the LLM landscape today) and "
            "'models' (array of exactly 10 items SORTED by rank ascending, where each item has: "
            "name, vendor, rank (int), popularity_notes (string), context_window (string), "
            "cost_input (string), cost_output (string), open_source (bool), "
            "strengths (list of strings), best_for (string), url (string))."
        ),
    },
    "repositories": {
        "title": "Model Repositories & Platforms",
        "prompt": (
            "Describe the major AI model repositories and deployment platforms: Hugging Face, "
            "Ollama, Replicate, Together AI, Fireworks AI, and AWS Bedrock. "
            "For each cover: purpose, number of models (approx), pricing model, "
            "key features, and who it is best suited for. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the model repository ecosystem) and "
            "'platforms' (array where each item has: "
            "name, purpose (string), model_count (string), pricing (string), "
            "features (list of strings), best_for (string), url (string))."
        ),
    },
    "databases": {
        "title": "AI in Major Databases",
        "prompt": (
            "Explain AI/ML capabilities built into these databases and data platforms: "
            "Snowflake (Cortex AI), Google BigQuery (BigQuery ML + Vertex AI), "
            "PostgreSQL (pgvector + pgai), Amazon (Aurora ML + Redshift ML), "
            "Databricks (MLflow + DBRX), and MongoDB Atlas Vector Search. "
            "For each cover: AI feature name, what it does, vector search support, "
            "LLM integration, and pricing notes. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of AI capabilities in modern databases) and "
            "'databases' (array where each item has: "
            "name, ai_feature (string), description (string), vector_search (bool), "
            "llm_integration (string), pricing_notes (string), url (string))."
        ),
    },
    "observability": {
        "title": "AI Observability, Cost & Monitoring",
        "prompt": (
            "Compare AI observability and cost monitoring tools: LangSmith, Helicone, "
            "Weights & Biases (W&B), Arize AI, LangFuse, and OpenLLMetry. "
            "For each cover: what it monitors, key features, pricing, and best use case. "
            "Also include 3-4 general tips for reducing LLM API costs. "
            "Return a JSON object with three keys: "
            "'summary' (2-3 sentence overview of why AI observability matters), "
            "'tools' (array with: name, monitors (string), features (list), pricing (string), best_for (string), url (string)), "
            "and 'cost_tips' (array of strings)."
        ),
    },
}

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")


def generate_section(key: str, section: dict, research_context: str = "") -> dict:
    print(f"  Generating: {section['title']}")
    context_block = ""
    if research_context:
        context_block = (
            f"## Live research data (fetched today)\n{research_context}\n\n"
            "Use the above as your primary source for current rankings, pricing, and adoption data. "
            "Supplement with your own knowledge where the research is incomplete.\n\n"
        )
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": (
                    f"{context_block}{section['prompt']}\n\n"
                    "Respond with ONLY valid JSON, no markdown fences, no explanation."
                ),
            }
        ],
    )
    raw = message.content[0].text.strip()
    data = json.loads(raw)
    data["_meta"] = {
        "title": section["title"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return data


def run_generation(sections: list = None):
    os.makedirs(CONTENT_DIR, exist_ok=True)
    targets = sections or list(SECTIONS.keys())
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting content generation...")

    research_data = {}
    if os.environ.get("TAVILY_API_KEY"):
        print("  Running web research...")
        from research import research_all
        research_data = research_all()
    else:
        print("  No TAVILY_API_KEY found — skipping web research.")

    for key in targets:
        try:
            data = generate_section(key, SECTIONS[key], research_data.get(key, ""))
            path = os.path.join(CONTENT_DIR, f"{key}.json")
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  Saved {path}")
        except Exception as e:
            print(f"  ERROR generating {key}: {e}")
    print("Done.")


if __name__ == "__main__":
    run_generation()
