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
            "List the TOP 10 AI code generation and agentic coding tools ranked by actual developer adoption. "
            "Be completely objective — base rankings on developer surveys (Stack Overflow, JetBrains), "
            "download stats, and public adoption data. Consider all major tools including: "
            "GitHub Copilot, Cursor, Claude Code, OpenAI Codex (the agentic coding agent, not the old model), "
            "Devin/Devin Desktop (by Cognition AI, formerly Windsurf), Codeium, Amazon CodeWhisperer, "
            "Tabnine, and others — include only what truly belongs in the top 10 by usage. "
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
    "image_gen": {
        "title": "AI Image Generation",
        "prompt": (
            "List the TOP 10 AI image generation tools ranked by actual user adoption and usage as of your knowledge cutoff. "
            "Be objective — base rankings on user counts, social media activity, API usage, and developer surveys. "
            "Include tools like Midjourney, DALL-E 3, Stable Diffusion, Flux, Adobe Firefly, Ideogram, "
            "Leonardo AI, Runway, Canva AI, and others that qualify. Only include what truly belongs in the top 10. "
            "For each tool cover: vendor, pricing (free tier + paid), key strengths, output quality, best use case, url. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the AI image generation landscape) and "
            "'tools' (array of up to 10 items SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "strengths (list of strings), best_for (string), url (string))."
        ),
    },
    "video_gen": {
        "title": "AI Video Generation",
        "prompt": (
            "List the TOP 10 AI video and movie generation tools ranked by actual user adoption as of your knowledge cutoff. "
            "Be objective — include tools like Sora (OpenAI), Runway ML, Pika Labs, Kling AI, Luma Dream Machine, "
            "HeyGen, Synthesia, Veo (Google), Udio, and others that qualify by actual usage. "
            "For each tool cover: vendor, pricing, key strengths, max video length/resolution, best use case, url. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the AI video generation landscape) and "
            "'tools' (array of up to 10 items SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "max_length (string), max_resolution (string), "
            "strengths (list of strings), best_for (string), url (string))."
        ),
    },
    "workspace": {
        "title": "AI Productivity & Workspace Tools",
        "prompt": (
            "List the TOP 10 AI productivity and workspace tools ranked by actual user adoption. "
            "These are tools that enhance knowledge work, research, writing, and business workflows — "
            "NOT coding tools. Include tools like: Google NotebookLM/Gemini Notebook, "
            "Microsoft Copilot for M365, Notion AI, Perplexity AI, Google Workspace AI (Gemini in Docs/Gmail), "
            "Grammarly AI, Otter.ai, Mem.ai, Glean, and others that qualify by actual usage. "
            "Be objective — rank by real adoption, user counts, and enterprise deployments. "
            "For each tool cover: vendor, pricing (free tier + paid), key capabilities, "
            "which apps/platforms it integrates with, best use case, and url. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of AI in productivity and workspace tools) and "
            "'tools' (array of up to 10 items SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "capabilities (list of strings), integrations (list of strings), best_for (string), url (string))."
        ),
    },
    "web_scrapers": {
        "title": "AI Web Scrapers & Browser Automation",
        "prompt": (
            "List the TOP 10 AI-powered web scraping and browser automation tools ranked by developer adoption. "
            "Include tools like Firecrawl, Apify, Browse.ai, Browserbase, AgentQL, Playwright with AI, "
            "Wave (Waveterm), Diffbot, Octoparse, and others that qualify. "
            "Be objective — rank by actual developer usage, GitHub stars, and community adoption. "
            "For each tool cover: vendor, pricing (free tier + paid), key strengths, "
            "AI capabilities (LLM-powered extraction, natural language queries, etc.), best use case, url. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of AI in web scraping and browser automation) and "
            "'tools' (array of up to 10 items SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "ai_features (list of strings), strengths (list of strings), best_for (string), url (string))."
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
            section_research = research_data.get(key, {})
            context = section_research.get("context", "") if isinstance(section_research, dict) else ""
            sources = section_research.get("sources", []) if isinstance(section_research, dict) else []
            data = generate_section(key, SECTIONS[key], context)
            if sources:
                data["sources"] = sources
            path = os.path.join(CONTENT_DIR, f"{key}.json")
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"  Saved {path}")
        except Exception as e:
            print(f"  ERROR generating {key}: {e}")
    print("Done.")


if __name__ == "__main__":
    run_generation()
