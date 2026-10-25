import os
import json
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

_RANK_RULE = (
    "Include between 10 and 15 tools. Start with the top 10 by adoption. "
    "Then check tools ranked #11–15: if their adoption is within ~25% of #10 (no clear gap), "
    "include them. Stop as soon as you see a significant drop-off. "
    "Never pad to 15 — only include beyond 10 when the numbers genuinely cluster together."
)

SECTIONS = {
    "code_tools": {
        "title": "Code Generation Tools",
        "prompt": (
            "List the TOP 10 AI code generation and agentic coding tools ranked by actual developer adoption. "
            "Be completely objective — base rankings on developer surveys (Stack Overflow, JetBrains), "
            "download stats, and public adoption data. Consider all major tools including: "
            "GitHub Copilot, Cursor, Claude Code, OpenAI Codex (the agentic coding agent, not the old model), "
            "Devin/Devin Desktop (by Cognition AI, formerly Windsurf), Codeium, Amazon CodeWhisperer, "
            "Tabnine, and others — rank all candidates then apply the cutoff rule below. "
            "For each tool cover: vendor, pricing (free tier + paid), key strengths, IDE support, "
            "best use case, and vendor website URL. "
            f"{_RANK_RULE} "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the AI code generation landscape) and "
            "'tools' (array SORTED by adoption rank, where each item has: "
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
            "HuggingFace download stats, and public adoption data. "
            "IMPORTANT: also factor in enterprise and aggregator reach — a model available through multiple "
            "cloud aggregators (AWS Bedrock, Azure OpenAI, Google Vertex AI, Snowflake Cortex, IBM watsonx) "
            "has significantly higher real-world adoption than its direct-API numbers suggest, because large "
            "enterprises consume AI through these secure platforms rather than vendor APIs directly. "
            "Weight aggregator coverage as a meaningful positive signal in the ranking. "
            "Include whichever models actually qualify; if they do not, omit them. "
            "For each model provide: name, vendor, context window, input/output cost per 1M tokens, "
            "open source flag, usage rank (integer 1=most used), popularity_notes (1 sentence citing the "
            "specific data or reason for this rank, including aggregator availability if relevant), "
            "key strengths (list), best use case, vendor website URL. "
            f"{_RANK_RULE} "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the LLM landscape today) and "
            "'models' (array SORTED by rank ascending, where each item has: "
            "name, vendor, rank (int), popularity_notes (string), context_window (string), "
            "cost_input (string), cost_output (string), open_source (bool), "
            "strengths (list of strings), best_for (string), url (string))."
        ),
    },
    "repositories": {
        "title": "Model Repositories & Platforms",
        "prompt": (
            "Describe the major open AI model repositories and developer inference platforms: "
            "Hugging Face, Ollama, Replicate, Together AI, Fireworks AI, SiliconFlow, and similar. "
            "These are open hubs and developer-facing inference APIs — NOT enterprise aggregators "
            "(Bedrock, Azure OpenAI) or MLOps platforms (SageMaker, Vertex AI), which are separate. "
            "For each cover: purpose, number of models (approx), pricing model, "
            "key features, and who it is best suited for. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the open model repository ecosystem) and "
            "'platforms' (array where each item has: "
            "name, purpose (string), model_count (string), pricing (string), "
            "features (list of strings), best_for (string), url (string))."
        ),
    },
    "enterprise_apis": {
        "title": "Enterprise Model APIs",
        "prompt": (
            "List and compare the major enterprise AI model API aggregators — cloud platforms that let "
            "corporations access foundation models (GPT, Claude, Llama, etc.) via a secure managed API "
            "without data leaving their cloud environment. "
            "Include: AWS Bedrock, Azure OpenAI Service, Google Vertex AI Model Garden, "
            "Snowflake Cortex AI, IBM watsonx, Cloudflare Workers AI, Oracle Cloud AI, and others. "
            "For each cover: which foundation models are available, data residency/compliance features, "
            "pricing model, key enterprise features (VPC, audit logs, fine-tuning support), and best_for. "
            "Also include a 'why_enterprises_use_aggregators' field explaining why companies use these "
            "instead of vendor APIs directly. "
            "Return a JSON object with three keys: "
            "'summary' (2-3 sentences on the enterprise model API landscape), "
            "'why_enterprises_use_aggregators' (list of 4-5 strings — reasons like data residency, "
            "compliance, single billing, existing cloud contracts), and "
            "'platforms' (array ranked by enterprise adoption, each with: "
            "name, vendor, rank (int), available_models (list of strings), "
            "data_residency (bool), compliance (list of strings), pricing (string), "
            "key_features (list of strings), best_for (string), url (string))."
        ),
    },
    "ml_platforms": {
        "title": "ML Training & Deployment Platforms",
        "prompt": (
            "List and compare the major end-to-end ML platforms used for training, fine-tuning, "
            "experimenting with, and deploying machine learning models at scale. "
            "Include: AWS SageMaker, Google Vertex AI (full platform), Azure Machine Learning, "
            "Databricks (MLflow + Mosaic AI), DataRobot, H2O.ai, Weights & Biases (as MLOps), "
            "Modal, and others that qualify by actual enterprise adoption. "
            "For each cover: what it does (training, deployment, experiment tracking, etc.), "
            "cloud provider, pricing model, who uses it, key differentiators, and url. "
            f"{_RANK_RULE} "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentences on the ML platform landscape and when you need one vs. just using a model API) and "
            "'platforms' (array ranked by enterprise adoption, each with: "
            "name, vendor, rank (int), cloud (string), capabilities (list of strings), "
            "supports_training (bool), supports_deployment (bool), pricing (string), "
            "best_for (string), url (string))."
        ),
    },
    "databases": {
        "title": "AI in Major Databases",
        "prompt": (
            "Explain AI/ML capabilities built into these databases and data platforms: "
            "Snowflake (Cortex AI), Google BigQuery (BigQuery ML + Vertex AI), "
            "PostgreSQL (pgvector + pgai), Amazon Aurora ML, Amazon Redshift ML, "
            "Databricks (Mosaic AI + Vector Search), and MongoDB Atlas Vector Search. "
            "Treat Aurora ML and Redshift ML as SEPARATE entries — they are different services. "
            "For vector_search: be precise — mark true ONLY if the platform has native built-in "
            "vector search. If support is only via a third-party extension (e.g. pgvector on Aurora), "
            "mark vector_search as false and explain in vector_search_notes. "
            "For the url field: provide the specific AI feature documentation page, "
            "NOT the generic product homepage. "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of AI capabilities in modern databases) and "
            "'databases' (array where each item has: "
            "name, ai_feature (string), description (string), vector_search (bool), "
            "vector_search_notes (string — clarify native vs extension vs not supported), "
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
            "Leonardo AI, Runway, Canva AI, and others that qualify — rank all candidates then apply the cutoff rule below. "
            "For each tool cover: vendor, pricing (free tier + paid), key strengths, output quality, best use case, url. "
            f"{_RANK_RULE} "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the AI image generation landscape) and "
            "'tools' (array SORTED by adoption rank, where each item has: "
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
            f"{_RANK_RULE} "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of the AI video generation landscape) and "
            "'tools' (array SORTED by adoption rank, where each item has: "
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
            "Grammarly AI, Otter.ai, Wave (wave.com, AI note taker & meeting recorder), "
            "Fireflies.ai, Fathom, Mem.ai, Glean, and others that qualify by actual usage. "
            "Be objective — rank by real adoption, user counts, and enterprise deployments. "
            "For each tool cover: vendor, pricing (free tier + paid), key capabilities, "
            "which apps/platforms it integrates with, best use case, and url. "
            f"{_RANK_RULE} "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of AI in productivity and workspace tools) and "
            "'tools' (array SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "capabilities (list of strings), integrations (list of strings), best_for (string), url (string))."
        ),
    },
    "llm_optimization": {
        "title": "LLM Cost & Performance Optimization",
        "prompt": (
            "Produce a practical guide to optimizing LLM usage for cost and performance at inference time "
            "(not training/fine-tuning). Cover the most impactful techniques developers actually use. "
            "For each technique include: name, description, typical token/cost savings (e.g. '30-60% reduction'), "
            "difficulty (Easy/Medium/Hard), works_with (list of providers it applies to), "
            "and a concrete example (1-2 sentences showing how to apply it). "
            "Also include a 'tools' list of real caching/optimization tools (e.g. GPTCache, LangChain, "
            "Helicone, Redis semantic cache, LiteLLM) with name, what it does, pricing, and url. "
            "Return a JSON object with four keys: "
            "'summary' (2-3 sentences on why optimization matters and typical savings achievable), "
            "'techniques' (array of optimization techniques, each with: name, description, savings (string), "
            "difficulty (string), works_with (list), example (string)), "
            "'tools' (array with: name, description, pricing_free (bool), pricing_paid (string), url (string)), "
            "'quick_wins' (list of 5 strings — the highest-impact, lowest-effort things to do first)."
        ),
    },
    "fine_tuning": {
        "title": "LLM Fine-Tuning Platforms",
        "prompt": (
            "List the TOP 10 platforms and tools for fine-tuning large language models, ranked by actual developer "
            "and enterprise adoption. Include managed cloud services and open-source frameworks. "
            "Consider: OpenAI Fine-Tuning API, Hugging Face AutoTrain, Together AI, Replicate, Modal, "
            "Vertex AI (Google), Amazon Bedrock fine-tuning, Axolotl, LLaMA-Factory, Unsloth, "
            "and others that qualify by actual usage. "
            "For each cover: vendor, supported base models, pricing model, whether it requires GPUs locally, "
            "key features, best use case (e.g. domain adaptation, instruction tuning, RLHF), and url. "
            "Also include a 'when_to_fine_tune' field (1 sentence on the right scenario to choose fine-tuning "
            "over RAG or prompt engineering). "
            f"{_RANK_RULE} "
            "Return a JSON object with three keys: "
            "'summary' (2-3 sentences on when fine-tuning makes sense vs RAG vs prompting), "
            "'when_to_fine_tune' (3-4 bullet points as a list of strings), and "
            "'tools' (array SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "supported_models (list of strings), requires_local_gpu (bool), "
            "features (list of strings), best_for (string), url (string))."
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
            f"{_RANK_RULE} "
            "Return a JSON object with two keys: "
            "'summary' (2-3 sentence overview of AI in web scraping and browser automation) and "
            "'tools' (array SORTED by adoption rank, where each item has: "
            "name, vendor, rank (int), pricing_free (bool), pricing_paid (string), "
            "ai_features (list of strings), strengths (list of strings), best_for (string), url (string))."
        ),
    },
}

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")

# Sections that have ranked items — eligible for dual-model cross-check
RANKED_SECTIONS = {
    "code_tools", "models", "image_gen", "video_gen",
    "web_scrapers", "workspace", "fine_tuning", "ml_platforms", "enterprise_apis",
}

# Key of the items array within each section's JSON
_ITEMS_KEY = {"models": "models", "enterprise_apis": "platforms", "ml_platforms": "platforms"}


def _items_key(key: str) -> str:
    return _ITEMS_KEY.get(key, "tools")


def _normalize(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", name.lower())


def generate_section(key: str, section: dict, research_context: str = "",
                     model: str = "claude-opus-4-8") -> dict:
    short = model.split("-")[1]  # "sonnet" or "opus"
    print(f"  Generating [{short}]: {section['title']}")
    context_block = ""
    if research_context:
        context_block = (
            f"## Live research data (fetched today)\n{research_context}\n\n"
            "Use the above as your primary source for current rankings, pricing, and adoption data. "
            "If the research mentions tools NOT listed in the prompt below that have significant adoption, "
            "include them — do not limit yourself only to the tools named in the prompt. "
            "Supplement with your own knowledge where the research is incomplete.\n\n"
        )
    message = client.messages.create(
        model=model,
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


def annotate_agreement(key: str, primary: dict, secondary: dict) -> dict:
    """Compare primary (Opus) and secondary (Sonnet) rankings; annotate agreement level."""
    ik = _items_key(key)
    primary_items = primary.get(ik, [])
    secondary_items = secondary.get(ik, [])

    secondary_lookup = {_normalize(item.get("name", "")): item.get("rank") for item in secondary_items}

    for item in primary_items:
        n = _normalize(item.get("name", ""))
        p_rank = item.get("rank")
        s_rank = secondary_lookup.get(n)
        item["sonnet_rank"] = s_rank
        if s_rank is None:
            item["rank_agreement"] = "excluded"   # Sonnet didn't include it
        elif abs(p_rank - s_rank) == 0:
            item["rank_agreement"] = "strong"
        elif abs(p_rank - s_rank) <= 2:
            item["rank_agreement"] = "minor"
        else:
            item["rank_agreement"] = "disagree"

    # Tools in Sonnet top-10 that Opus didn't include
    primary_names = {_normalize(item.get("name", "")) for item in primary_items}
    additions = [
        item["name"] for item in secondary_items
        if item.get("rank", 99) <= 10 and _normalize(item.get("name", "")) not in primary_names
    ]
    if additions:
        primary["notable_sonnet_additions"] = additions

    primary["cross_checked"] = True
    return primary


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

    def _generate_and_save(key):
        section_research = research_data.get(key, {})
        context = section_research.get("context", "") if isinstance(section_research, dict) else ""
        sources = section_research.get("sources", []) if isinstance(section_research, dict) else []

        if key in RANKED_SECTIONS:
            # Opus is primary (more accurate); Sonnet cross-checks
            with ThreadPoolExecutor(max_workers=2) as ex:
                f_opus = ex.submit(generate_section, key, SECTIONS[key], context, "claude-opus-4-8")
                f_sonnet = ex.submit(generate_section, key, SECTIONS[key], context, "claude-sonnet-4-6")
                data = f_opus.result()
                sonnet_data = f_sonnet.result()
            data = annotate_agreement(key, data, sonnet_data)
        else:
            data = generate_section(key, SECTIONS[key], context)

        if sources:
            data["sources"] = sources
        path = os.path.join(CONTENT_DIR, f"{key}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Saved {path}")

    with ThreadPoolExecutor(max_workers=len(targets)) as executor:
        futures = {executor.submit(_generate_and_save, key): key for key in targets}
        for future in as_completed(futures):
            key = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"  ERROR generating {key}: {e}")
    print("Done.")


if __name__ == "__main__":
    run_generation()
