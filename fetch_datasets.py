"""Standalone tool: fetch public malicious/jailbreak prompt datasets from
the internet and GitHub, and save them as plain JSON/CSV files.

This is intentionally independent of any other project — it just produces
flat data files in ./data/. Point any other tool at those files later.

Fetching is delegated to Microsoft's PyRIT library (https://github.com/
Azure/PyRIT), which maintains a registry of known red-teaming datasets
(AdvBench, HarmBench, JailbreakBench/JBB-Behaviors, the In-The-Wild /
Forbidden-Questions jailbreak corpus, and more) so we don't have to
hand-maintain fragile scrapers for each one's URL/CSV format.

Usage:
    pip install -r requirements.txt

    python fetch_datasets.py --list                      # show what's available
    python fetch_datasets.py --all                       # fetch everything
    python fetch_datasets.py --datasets harmbench advbench

Output: one file per dataset in ./data/<dataset_name>.json, each a list of:
    {"id": "...", "prompt": "...", "category": "...",
     "source_dataset": "...", "license_note": "..."}

LICENSING / USAGE NOTE: these datasets are published for defensive
AI-safety research (training/evaluating guardrails, robustness
benchmarking, authorized red-teaming of your own systems). Check each
dataset's own license/terms before using the output elsewhere — some
require explicitly accepting conditions before they can be downloaded.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def list_available() -> None:
    from pyrit.datasets import SeedDatasetProvider

    names = await SeedDatasetProvider.get_all_dataset_names_async()
    print(f"{len(names)} datasets registered in PyRIT:")
    for n in sorted(names):
        print(f"  - {n}")


async def fetch_and_write(dataset_names: list[str] | None) -> None:
    from pyrit.setup.initialization import IN_MEMORY, initialize_pyrit_async
    from pyrit.datasets import SeedDatasetProvider

    await initialize_pyrit_async(memory_db_type=IN_MEMORY)
    os.makedirs(DATA_DIR, exist_ok=True)

    datasets = await SeedDatasetProvider.fetch_datasets_async(dataset_names=dataset_names)

    manifest = []
    for dataset in datasets:
        dataset_name = getattr(dataset, "dataset_name", None) or "unknown_dataset"
        slug = _slug(dataset_name)
        out_path = os.path.join(DATA_DIR, f"{slug}.json")

        records = []
        for i, seed in enumerate(dataset.seeds):
            prompt_text = getattr(seed, "value", None) or getattr(seed, "prompt", None) or str(seed)
            categories = getattr(seed, "harm_categories", None) or []
            category = categories[0] if categories else "uncategorized"
            records.append(
                {
                    "id": f"{slug}-{i:04d}",
                    "prompt": prompt_text,
                    "category": category,
                    "source_dataset": dataset_name,
                    "license_note": "defensive AI-safety research only; see source dataset's own license/terms",
                }
            )

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        print(f"Wrote {len(records)} prompts from '{dataset_name}' -> {out_path}")
        manifest.append({"dataset": dataset_name, "file": os.path.basename(out_path), "count": len(records)})

    with open(os.path.join(DATA_DIR, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nWrote manifest -> {os.path.join(DATA_DIR, '_manifest.json')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List all datasets PyRIT knows about.")
    group.add_argument("--all", action="store_true", help="Fetch every registered dataset.")
    group.add_argument("--datasets", nargs="+", help="Fetch only these dataset names.")
    args = parser.parse_args()

    try:
        if args.list:
            asyncio.run(list_available())
        elif args.all:
            asyncio.run(fetch_and_write(None))
        else:
            asyncio.run(fetch_and_write(args.datasets))
    except ImportError:
        print("PyRIT isn't installed. Run: pip install -r requirements.txt", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
