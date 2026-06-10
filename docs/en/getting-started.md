# Getting Started

This guide gets ShotForge running locally and explains what to inspect after the
first run.

## Install

```powershell
git clone https://github.com/whaidushu/ShotForge.git
cd ShotForge
conda create -n ShotForge python=3.11 pip -y
conda activate ShotForge
pip install -r requirements.txt
pip install -e .
```

For development tools:

```powershell
pip install -e ".[dev]"
```

## Configure

Create a local environment file:

```powershell
copy .env.example .env
```

You can run the demo and design-only workflows without real model services.
Full video generation needs configured providers. See
[Configuration](configuration.md) and [Providers](providers.md).

## Run Checks

```powershell
ruff check src tests
pytest -q
```

Run provider and storage checks:

```powershell
shotforge doctor --deep
```

## Start The Web App

```powershell
shotforge web --reload
```

Open:

```text
http://127.0.0.1:8000
```

The demo page is useful when model services are not configured yet:

```text
http://127.0.0.1:8000/demo?language=en
```

## First Web Flow

1. Open Configuration.
2. Create or select a provider profile.
3. Run preflight.
4. Return to Workflow.
5. Enter an idea.
6. Run design or full-loop mode.
7. Inspect storyboard, prompt package, generated artifacts, evaluation issues,
   version changes, and exports.

## CLI Examples

Design-only:

```powershell
shotforge design "A neon train crossing a desert at sunrise" --language en
```

Full loop:

```powershell
shotforge full-loop "A product reveal shot in a rainy city street" --language en --generator <provider-id>
```

Full loop with iterative redesign:

```powershell
shotforge full-loop "A product reveal shot in a rainy city street" --language en --redesign --max-iterations 3 --generator <provider-id>
```

Inspect a saved package:

```powershell
shotforge inspect data/runs/{run_id}/package.json
shotforge audit data/runs/{run_id}/package.json
```

## Output Location

Run outputs are written under:

```text
data/runs/{run_id}
```

Common files:

- `package.json`
- `package_view.json`
- `package.csv`
- `package.md`
- `manifest.json`
- `trace.json`
- `run_summary.md`
- `evaluation.csv`
- generated videos
- prompt text and prompt JSON
- workflow payloads
- extracted frames

## What To Check After A Run

- `GET /api/runs/{run_id}/workbench` for product-level status.
- `GET /api/runs/{run_id}/generation-artifacts` for artifact links.
- `GET /api/runs/{run_id}/runtime-evidence` for runtime evidence.
- `GET /api/runs/{run_id}/versions` for version snapshots.
- `data/runs/{run_id}/package.json` for the full saved state.
