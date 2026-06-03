from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_DIR = ROOT / "data" / "runs"
SAMPLE_RUN_IDS = {"en": "shotforge_gold_sample", "zh": "shotforge_gold_sample_zh"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy the curated ShotForge gold sample into the local runs directory.",
    )
    parser.add_argument(
        "--sample-dir",
        type=Path,
        default=None,
        help="Source sample directory. Defaults to the gold sample for --language.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help="Target runs directory. Defaults to data/runs.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing local gold sample run.",
    )
    parser.add_argument(
        "--language",
        choices=("zh", "en"),
        default="en",
        help="Language query parameter printed for the web URL.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sample_dir = (
        args.sample_dir
        or ROOT / "examples" / "demo_runs" / SAMPLE_RUN_IDS[args.language]
    ).resolve()
    run_id = sample_dir.name
    target_dir = (args.runs_dir / run_id).resolve()

    if not (sample_dir / "package.json").exists():
        raise SystemExit(f"Sample package not found: {sample_dir / 'package.json'}")
    if target_dir.exists():
        if not args.force:
            raise SystemExit(
                f"Target already exists: {target_dir}\n"
                "Run again with --force to replace the local sample."
            )
        shutil.rmtree(target_dir)

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sample_dir, target_dir)
    _rewrite_export_paths(target_dir, run_id)

    print(f"Seeded sample run: {target_dir}")
    print(f"Open: http://127.0.0.1:8000/?run_id={run_id}&language={args.language}")


def _rewrite_export_paths(target_dir: Path, run_id: str) -> None:
    package_path = target_dir / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["run_id"] = run_id
    for export in package.get("exports", []):
        filename = _filename_for_export(export.get("format", ""))
        if filename:
            export["path"] = str(target_dir / filename)
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")


def _filename_for_export(export_format: str) -> str:
    return {
        "json": "package.json",
        "csv": "package.csv",
        "markdown": "package.md",
        "evaluation_csv": "evaluation.csv",
        "manifest": "manifest.json",
        "package_view": "package_view.json",
        "trace": "trace.json",
        "run_summary": "run_summary.md",
    }.get(export_format, "")


if __name__ == "__main__":
    main()
