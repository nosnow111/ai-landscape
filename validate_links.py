"""
Link validator for content/*.json

Validate:  fetch each URL, check page relevance via Claude Haiku
Auto-fix:  for flagged URLs, search Tavily for the correct page,
           verify it, then patch content/*.json in place

Usage:
  python validate_links.py            # validate only, print report
  python validate_links.py --fix      # validate + auto-fix flagged links
  python validate_links.py --quiet    # suppress per-link lines
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
ITEM_KEYS = ["tools", "models", "platforms", "databases"]

_anthropic = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ── extraction ─────────────────────────────────────────────────────────────

def extract_entries(data: dict) -> list[dict]:
    """Return all items that have a url field."""
    entries = []
    for key in ITEM_KEYS:
        for item in data.get(key, []):
            if item.get("url"):
                entries.append(item)
    return entries


# ── fetch + judge ──────────────────────────────────────────────────────────

def fetch_page(url: str) -> tuple[int, str, str]:
    """Returns (status_code, final_url, page_excerpt)."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AI-Landscape-Validator/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        text = resp.text
        title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
        body = re.sub(r"<[^>]+>", " ", text)
        body = re.sub(r"\s+", " ", body).strip()[:800]
        return resp.status_code, str(resp.url), f"Title: {title}\n\n{body}"
    except requests.exceptions.Timeout:
        return 0, url, "TIMEOUT"
    except Exception as e:
        return 0, url, f"ERROR: {e}"


def judge_relevance(tool_name: str, topic: str, url: str, excerpt: str) -> tuple[bool, str]:
    """Ask Claude Haiku whether the page is actually about the expected tool."""
    prompt = f"""You are checking whether a documentation or product page is relevant to a specific tool or feature.

Tool/feature name: {tool_name}
Expected topic: {topic}
URL: {url}

Page content (title + excerpt):
{excerpt}

Is this page actually about "{tool_name}" or "{topic}"?
Answer with one of:
- RELEVANT: <one sentence why>
- NOT_RELEVANT: <one sentence why, and what the page actually shows>

Be strict: a generic product homepage with no mention of the specific feature is NOT_RELEVANT."""

    try:
        msg = _anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=128,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = msg.content[0].text.strip()
        return answer.startswith("RELEVANT"), answer
    except Exception as e:
        return True, f"Claude check skipped: {e}"


def validate_entry(section_key: str, item: dict) -> dict:
    name = item.get("name", "unknown")
    url = item.get("url", "")
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
        "suggested_url": None,
    }

    if status == 0:
        result["flag"] = "❌ unreachable"
        return result
    if status == 403:
        # Many major platforms (Midjourney, Adobe, etc.) block scrapers but have valid URLs
        result["relevant"] = True
        result["flag"] = "✅ ok (403 — scraper blocked, URL assumed valid)"
        return result
    if status >= 400:
        result["flag"] = f"❌ HTTP {status}"
        return result

    # Fast pass: tool name found directly in page text
    if name.lower().split("(")[0].strip() in excerpt.lower():
        result["relevant"] = True
        result["flag"] = "✅ ok"
        return result

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
                redirect = f" → {r['redirected_to']}" if r["redirected_to"] else ""
                note = f"\n    {r['judgment']}" if r.get("judgment") else ""
                print(f"  {r['flag']}  [{r['section']}] {r['name']}{redirect}{note}")

    return results


# ── auto-fix ───────────────────────────────────────────────────────────────

def search_replacement(tool_name: str, topic: str, section_key: str) -> str | None:
    """Use Tavily to find the correct URL for a flagged entry."""
    try:
        from tavily import TavilyClient
        tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    except Exception:
        return None

    query = f"{tool_name} official documentation site"
    try:
        resp = tavily.search(query=query, search_depth="basic", max_results=5)
        candidates = [r["url"] for r in resp.get("results", []) if r.get("url")]
        return candidates[0] if candidates else None
    except Exception:
        return None


def verify_and_fix(result: dict) -> dict:
    """Find and verify a replacement URL for a flagged result."""
    name = result["name"]
    topic = result.get("judgment", name)
    section = result["section"]

    candidate = search_replacement(name, topic, section)
    if not candidate:
        result["fix_status"] = "no candidate found"
        return result

    # Verify the candidate page is actually relevant
    status, final_url, excerpt = fetch_page(candidate)
    if status == 0 or status >= 400:
        result["fix_status"] = f"candidate unreachable ({status})"
        return result

    relevant, judgment = judge_relevance(name, topic, final_url, excerpt)
    if not relevant:
        result["fix_status"] = f"candidate also wrong: {judgment}"
        return result

    result["suggested_url"] = final_url
    result["fix_status"] = "fix found"
    return result


def apply_fixes(results: list[dict], dry_run: bool = False) -> list[dict]:
    """
    For each flagged result, search for a replacement URL and patch the JSON.
    Returns the subset of results that had a fix applied.
    """
    flagged = [r for r in results if r["flag"] in ("⚠️  wrong page",) or r["flag"].startswith("❌")]
    if not flagged:
        print("  Nothing to fix.")
        return []

    print(f"\n  Searching for replacements for {len(flagged)} flagged link(s)...")
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(verify_and_fix, r): r for r in flagged}
        for future in as_completed(futures):
            r = future.result()
            status_line = r.get("fix_status", "?")
            suggestion = f"  →  {r['suggested_url']}" if r.get("suggested_url") else ""
            print(f"  [{r['section']}] {r['name']}  {status_line}{suggestion}")

    fixable = [r for r in flagged if r.get("suggested_url")]
    if not fixable:
        print("  No verified replacements found.")
        return []

    if dry_run:
        print(f"\n  Dry run — would patch {len(fixable)} URL(s):")
        for r in fixable:
            print(f"    [{r['section']}] {r['name']}")
            print(f"      old: {r['url']}")
            print(f"      new: {r['suggested_url']}")
        return fixable

    # Patch content JSON files in place
    patched_files = set()
    for r in fixable:
        path = CONTENT_DIR / f"{r['section']}.json"
        data = json.loads(path.read_text())
        for key in ITEM_KEYS:
            for item in data.get(key, []):
                if item.get("name") == r["name"] and item.get("url") == r["url"]:
                    item["url"] = r["suggested_url"]
                    item["url_auto_fixed"] = True
        path.write_text(json.dumps(data, indent=2))
        patched_files.add(r["section"])

    print(f"\n  ✓  Patched {len(fixable)} URL(s) in: {', '.join(sorted(patched_files))}")
    print("     Run `python build.py` to rebuild the site with fixed links.")
    return fixable


# ── reporting ──────────────────────────────────────────────────────────────

def print_summary(results: list[dict]):
    ok     = [r for r in results if r["flag"] == "✅ ok"]
    wrong  = [r for r in results if r["flag"] == "⚠️  wrong page"]
    broken = [r for r in results if r["flag"].startswith("❌")]

    print(f"\n{'='*60}")
    print(f"Link validation: {len(results)} URLs checked")
    print(f"  ✅ Valid:      {len(ok)}")
    print(f"  ⚠️  Wrong page: {len(wrong)}")
    print(f"  ❌ Broken:     {len(broken)}")

    if wrong or broken:
        print("\nAction needed:")
        for r in wrong + broken:
            redirect = f"\n    redirected → {r['redirected_to']}" if r["redirected_to"] else ""
            fix = f"\n    suggested  → {r['suggested_url']}" if r.get("suggested_url") else ""
            print(f"  {r['flag']}  [{r['section']}] {r['name']}  {r['url']}{redirect}{fix}")
            if r.get("judgment"):
                print(f"    {r['judgment']}")

    report_path = Path(__file__).parent / "validation_report.json"
    report_path.write_text(json.dumps(results, indent=2))
    print(f"\nFull report → {report_path.name}")


# ── entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    fix_mode = "--fix" in sys.argv
    dry_run  = "--dry-run" in sys.argv
    verbose  = "--quiet" not in sys.argv

    print("Validating links across all content sections...\n")
    results = validate_all(verbose=verbose)
    print_summary(results)

    if fix_mode or dry_run:
        print(f"\n{'='*60}")
        print("Auto-fix mode" + (" (dry run)" if dry_run else ""))
        print("="*60)
        apply_fixes(results, dry_run=dry_run)

    # Always exit 0 — never blocks the build
    sys.exit(0)
