#!/usr/bin/env python3
"""
AI Landscape content pipeline — orchestrator with 4 checkpoint stages.

  Stage 1  RESEARCH   Tavily web search for all sections in parallel
  Stage 2  GENERATE   Opus primary + Sonnet cross-check, parallel per section
  Stage 3  VALIDATE   Link relevance check — advisory, never blocks
  Stage 4  BUILD      Render docs/index.html

Each stage writes a checkpoint to checkpoints/<stage>.json when it completes.
On the next run, completed stages are skipped automatically.

Usage
-----
  python pipeline.py                     # run all stages; skip any already checkpointed
  python pipeline.py --from=generate    # re-run from generate stage onward
  python pipeline.py --from=validate    # re-run only validate + build
  python pipeline.py --only=build       # run exactly one stage
  python pipeline.py --force            # ignore all checkpoints, run everything
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
CHECKPOINT_DIR = ROOT / "checkpoints"
CONTENT_DIR = ROOT / "content"
RESEARCH_CACHE = CHECKPOINT_DIR / "research_data.json"

STAGES = ["research", "generate", "validate", "build"]


# ── helpers ────────────────────────────────────────────────────────────────

def ts() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


def divider(char="─", width=62):
    print(char * width)


def stage_banner(name: str, subtitle: str):
    divider("═")
    print(f"  [{ts()}]  STAGE {STAGES.index(name)+1}/4 · {name.upper()}")
    print(f"  {subtitle}")
    divider("═")


def save_checkpoint(stage: str, data: dict = None):
    CHECKPOINT_DIR.mkdir(exist_ok=True)
    payload = {
        "stage": stage,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        **(data or {}),
    }
    (CHECKPOINT_DIR / f"{stage}.json").write_text(json.dumps(payload, indent=2))
    print(f"\n  ✓  checkpoint saved  →  checkpoints/{stage}.json")


def load_checkpoint(stage: str) -> dict:
    p = CHECKPOINT_DIR / f"{stage}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def checkpoint_complete(stage: str) -> bool:
    if not (CHECKPOINT_DIR / f"{stage}.json").exists():
        return False
    if stage == "generate":
        # Verify each content file exists and ranked sections have cross_checked flag
        from generator import SECTIONS, RANKED_SECTIONS
        for key in SECTIONS:
            cf = CONTENT_DIR / f"{key}.json"
            if not cf.exists():
                return False
            if key in RANKED_SECTIONS:
                d = json.loads(cf.read_text())
                if not d.get("cross_checked"):
                    return False
    return True


# ── stage runners ──────────────────────────────────────────────────────────

def stage_research() -> dict:
    stage_banner("research", "Tavily web search — all sections queried in parallel")
    from research import research_all, QUERIES

    print(f"  Sections:  {len(QUERIES)}")
    t0 = time.time()
    data = research_all()
    elapsed = time.time() - t0

    CHECKPOINT_DIR.mkdir(exist_ok=True)
    RESEARCH_CACHE.write_text(json.dumps(data, indent=2))
    print(f"\n  Completed {len(data)} sections in {elapsed:.1f}s")
    save_checkpoint("research", {"sections": len(data), "elapsed_s": round(elapsed, 1)})
    return data


def stage_generate(research_data: dict = None):
    stage_banner("generate", "Opus primary · Sonnet cross-check — sections run in parallel")
    from generator import run_generation, SECTIONS, RANKED_SECTIONS

    if research_data is None and RESEARCH_CACHE.exists():
        print("  Loading research from checkpoint cache...")
        research_data = json.loads(RESEARCH_CACHE.read_text())

    # Determine which sections still need work
    done, todo = [], []
    for key in SECTIONS:
        cf = CONTENT_DIR / f"{key}.json"
        if cf.exists():
            d = json.loads(cf.read_text())
            if key not in RANKED_SECTIONS or d.get("cross_checked"):
                done.append(key)
                continue
        todo.append(key)

    if done:
        print(f"  ⏭  Skipping {len(done)} already-complete sections")
    if not todo:
        print("  All sections already generated.")
        save_checkpoint("generate", {"generated": [], "skipped": done})
        return

    print(f"\n  Workers:")
    for key in todo:
        tag = "[opus+sonnet]" if key in RANKED_SECTIONS else "[opus only] "
        print(f"    {tag}  {key}")

    t0 = time.time()
    run_generation(sections=todo, research_data=research_data)
    elapsed = time.time() - t0

    print(f"\n  Generated {len(todo)} sections in {elapsed:.1f}s")
    save_checkpoint("generate", {
        "generated": todo,
        "skipped": done,
        "elapsed_s": round(elapsed, 1),
    })


def stage_validate():
    stage_banner("validate", "Link relevance check + auto-fix — advisory, never blocks build")
    import validate_links

    results = validate_links.validate_all(verbose=True)
    validate_links.print_summary(results)

    # Auto-fix flagged links using Tavily search
    fixed = validate_links.apply_fixes(results, dry_run=False)

    ok = sum(1 for r in results if r["flag"] == "✅ ok")
    flagged = len(results) - ok
    save_checkpoint("validate", {
        "total": len(results),
        "ok": ok,
        "flagged": flagged,
        "auto_fixed": len(fixed),
    })


def stage_build():
    stage_banner("build", "Rendering docs/index.html from content/*.json")
    import build

    build.build()
    save_checkpoint("build", {"output": "docs/index.html"})


# ── orchestrator ───────────────────────────────────────────────────────────

RUNNERS = {
    "research": stage_research,
    "generate": stage_generate,
    "validate": stage_validate,
    "build": stage_build,
}


def main():
    parser = argparse.ArgumentParser(
        description="AI Landscape content pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--from", dest="from_stage", choices=STAGES, metavar="STAGE",
        help="Re-run from this stage onward (ignore earlier checkpoints)",
    )
    parser.add_argument(
        "--only", choices=STAGES, metavar="STAGE",
        help="Run exactly one stage regardless of checkpoints",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Ignore all checkpoints and run every stage",
    )
    args = parser.parse_args()

    # Print header
    print()
    divider("═")
    print(f"  AI Landscape Pipeline  ·  {ts()}")
    divider()
    print(f"  Stages: {' → '.join(s.upper() for s in STAGES)}")
    if args.only:
        print(f"  Mode:   single stage ({args.only.upper()})")
    elif args.force:
        print(f"  Mode:   force — all checkpoints ignored")
    elif args.from_stage:
        print(f"  Mode:   restart from {args.from_stage.upper()} onward")
    else:
        print(f"  Mode:   resume — skip completed checkpoints")
    divider("═")

    research_data = None

    for stage in STAGES:
        # --only: skip everything except the named stage
        if args.only and stage != args.only:
            continue

        # Determine whether to skip this stage
        force_from_here = args.force or (
            args.from_stage and STAGES.index(stage) >= STAGES.index(args.from_stage)
        )
        if not force_from_here and checkpoint_complete(stage):
            cp = load_checkpoint(stage)
            print(f"\n  ⏭  {stage.upper()} — completed at {cp.get('completed_at','?')}, skipping")
            continue

        # Run the stage
        if stage == "research":
            research_data = stage_research()
        elif stage == "generate":
            stage_generate(research_data)
        elif stage == "validate":
            stage_validate()
        elif stage == "build":
            stage_build()

    print()
    divider("═")
    print(f"  [{ts()}]  Pipeline finished.")
    divider("═")
    print()


if __name__ == "__main__":
    main()
