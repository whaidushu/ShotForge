## Demo Runs

`demo_runs/shotforge_gold_sample` and `demo_runs/shotforge_gold_sample_zh` are
curated public samples for the ShotForge workbench. They demonstrate:

- concrete storyboard beats for a short AI video concept;
- test generation, prompt evaluation, iterative redesign, and version diffs;
- lightweight public exports in JSON, CSV, Markdown, manifest, and run summary formats.

The public samples intentionally omit local execution traces and package-view
snapshots because those files can contain machine-local paths from the run that
created them.

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
