## Demo Runs

`demo_runs/shotforge_gold_sample` and `demo_runs/shotforge_gold_sample_zh` are
curated public samples for the ShotForge workbench. They demonstrate:

- concrete storyboard beats for a short AI video concept;
- test generation, prompt evaluation, iterative redesign, and version diffs;
- export artifacts in JSON, CSV, Markdown, manifest, package view, trace, and run summary formats.

Seed it into the local workspace:

```powershell
python scripts/seed_gold_sample.py --force
python scripts/seed_gold_sample.py --language zh --force
shotforge web
```

Then open:

```text
http://127.0.0.1:8000/?run_id=shotforge_gold_sample&language=en
http://127.0.0.1:8000/?run_id=shotforge_gold_sample_zh&language=zh
```
