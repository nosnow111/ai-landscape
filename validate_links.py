"""
Link validator for content/*.json
- Fetches each URL, follows redirects
- Checks page title/content for tool name relevance
- Flags bad status, wrong-page redirects
- Uses Claude to judge ambiguous cases
- Never blocks the build; always exits 0
"""

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv()

CONTENT_DIR = Path(__file__).parent / "content"
TIMEOUT = 10
MAX_WORKERS = 20

# Keys that hold items with URLs across all section types
ITEM_KEYS = ["tools", "models", "platforms", "databases"]

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def extract_entries(data: dict) -> list[dict]:
    """Return all items that have a url field."""
    entries = []
    for key in ITEM_KEYS:
        for item in data.get(key, []):
            if item.get("url"):
                entries.append(item)
    return entries


def fetch_page(url: str) -> tuple[int, str, str]:
    """Returns (status_code, final_url, page_text_excerpt)"""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AI-Landscape-Validator/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        # Extract title + first ~800 chars of visible text
        text = resp.text
        title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
        # Strip tags for body excerpt
        body = re.sub(r"<[^>]+>", " ", text)
        body = re.sub(r"\s+", " ", body).strip()[:800]
        excerpt = f"Title: {title}\n\n{body}"
        return resp.status_code, str(resp.url), excerpt
    except requests.exceptions.Timeout:
        return 0, url, "TIMEOUT"
    except Exception as e:
        return 0, url, f"ERROR: {e}"


def judge_relevance(tool_name: str, expected_topic: str, url: str, page_excerpt: str) -> tuple[bool, str]:
    """Ask Claude whether the page is actually about the expected tool/feature."""
    prompt = f"""You are checking whether a documentation or product page is relevant to a specific tool or feature.

Tool/feature name: {tool_name}
Expected topic: {expected_topic}
URL: {url}

Page content (title + excerpt):
{page_excerpt}

Is this page actually about "{tool_name}" or "{expected_topic}"?
Answer with one of:
- RELEVANT: <one sentence why>
- NOT_RELEVANT: <one sentence why, and what the page actually shows>

Be strict: a generic product homepage with no mention of the specific feature is NOT_RELEVANT."""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=128,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = msg.content[0].text.strip()
        relevant = answer.startswith("RELEVANT")
        return relevant, answer
    except Exception as e:
        return True, f"Claude check skipped: {e}"


def validate_entry(section_key: str, item: dict) -> dict:
    name = item.get("name", "unknown")
    url = item.get("url", "")
    # Use description or ai_feature as the expected topic hint
    topic = item.get("ai_feature") or item.get("description", "")[:120] or name

    status, final_url, excerpt = fetch_page(url)

    result = {
        "section": section_key,
        "name": name,
        "url": url,
        "status": status,
        "redirected_to": final_url if final_url != url else None,
        "relevant": None,
        "judgment": None,
        "flag": None,
    }

    if status == 0:
        result["flag"] = "❌ unreachable"
        return result

    if status >= 400:
        result["flag"] = f"❌ HTTP {status}"
        return result

    # Name appears directly in page text — fast pass
    if name.lower().split("(")[0].strip() in excerpt.lower():
        result["relevant"] = True
        result["flag"] = "✅ ok"
        return result

    # Otherwise ask Claude
    relevant, judgment = judge_relevance(name, topic, final_url, excerpt)
    result["relevant"] = relevant
    result["judgment"] = judgment
    result["flag"] = "✅ ok" if relevant else "⚠️  wrong page"
    return result


def validate_all(verbose: bool = True) -> list[dict]:
    tasks = []
    for path in sorted(CONTENT_DIR.glob("*.json")):
        key = path.stem
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        for item in extract_entries(data):
            tasks.append((key, item))

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(validate_entry, k, item): (k, item) for k, item in tasks}
        for future in as_completed(futures):
            r = future.result()
            results.append(r)
            if verbose:
                redirect = f" → {r['redirected_to']}" if r['redirected_to'] else ""
                judgment = f"\n    {r['judgment']}" if r.get('judgment') else ""
                print(f"  {r['flag']}  [{r['section']}] {r['name']}{redirect}{judgment}")

    return results


def print_summary(results: list[dict]):
    ok = [r for r in results if r["flag"] == "✅ ok"]
    wrong = [r for r in results if r["flag"] == "⚠️  wrong page"]
    broken = [r for r in results if r["flag"].startswith("❌")]

    print(f"\n{'='*60}")
    print(f"Link validation summary: {len(results)} URLs checked")
    print(f"  ✅ Valid:      {len(ok)}")
    print(f"  ⚠️  Wrong page: {len(wrong)}")
    print(f"  ❌ Broken:     {len(broken)}")

    if wrong or broken:
        print("\nAction needed:")
        for r in wrong + broken:
            redirect = f"\n    redirected → {r['redirected_to']}" if r['redirected_to'] else ""
            print(f"  {r['flag']}  [{r['section']}] {r['name']}  {r['url']}{redirect}")
            if r.get("judgment"):
                print(f"    {r['judgment']}")

    # Write machine-readable report
    report_path = Path(__file__).parent / "validation_report.json"
    report_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull report written to {report_path.name}")


if __name__ == "__main__":
    verbose = "--quiet" not in sys.argv
    print("Validating links across all content sections...\n")
    results = validate_all(verbose=verbose)
    print_summary(results)
    # Always exit 0 — validation is advisory, never blocks the build
    sys.exit(0)
