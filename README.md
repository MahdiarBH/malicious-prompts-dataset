# Malicious / Jailbreak Prompt Dataset Extraction

Standalone tool — fetches known public jailbreak / harmful-behavior
prompt datasets from the internet and GitHub, and saves them as flat
JSON files. Not tied to any other project.

## Why PyRIT instead of scraping each dataset ourselves

Hand-writing a scraper per dataset (parsing a specific CSV at a specific
GitHub path, or a specific HuggingFace dataset config) is fragile — those
URLs and formats change. [PyRIT](https://github.com/Azure/PyRIT),
Microsoft's AI red-teaming toolkit, already maintains a registry of these
datasets with stable loaders and caching, covering at least:

- **AdvBench** — ~520 adversarial prompts
- **HarmBench** — standardized red-teaming/refusal evaluation behaviors
- **JailbreakBench (JBB-Behaviors)** — 100 harmful + 100 benign behaviors
- **Forbidden Questions / In-The-Wild jailbreak prompts** — prompts collected from Reddit/Discord/websites
- and others — run `--list` to see everything currently registered

## Usage

```bash
pip install -r requirements.txt

# See what's available
python fetch_datasets.py --list

# Fetch everything
python fetch_datasets.py --all

# Or just specific datasets
python fetch_datasets.py --datasets harmbench advbench
```

## Output

One file per dataset in `data/`:

```
data/
  harmbench.json
  advbench.json
  jailbreakbench-jbb-behaviors.json
  _manifest.json        <- summary: which datasets, how many prompts each
```

Each entry:
```json
{
  "id": "harmbench-0007",
  "prompt": "...",
  "category": "...",
  "source_dataset": "HarmBench",
  "license_note": "defensive AI-safety research only; see source dataset's own license/terms"
}
```

## Licensing / usage note

These datasets are published specifically for **defensive AI-safety
research** — training/evaluating guardrails, robustness benchmarking,
authorized red-teaming of your own systems. Before using the output
elsewhere:

- Check each dataset's own license (most are MIT/Apache/ODC-BY — see each
  dataset's source repo/card).
- Some datasets are **gated** (e.g. on HuggingFace) and require accepting
  terms/conditions, and possibly a HuggingFace access token, before PyRIT
  can download them — if `--all` or `--datasets` fails on one of these,
  that's why.
- Don't redistribute raw dataset content beyond what each dataset's own
  terms allow.
