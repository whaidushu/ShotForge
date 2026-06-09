# Getting Started

This guide gets ShotForge running locally with the built-in development path.

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

## Run Checks

```powershell
ruff check src tests
pytest -q
```

## Start The Web App

```powershell
shotforge web --reload
```

Open:

```text
http://127.0.0.1:8000
```

The demo page is useful when local model services are not configured yet:

```text
http://127.0.0.1:8000/demo?language=en
```

## Run The CLI

```powershell
shotforge design "A cyber cat chases a glowing drone across rainy Shanghai rooftops" --language en
shotforge full-loop "A neon train crossing a desert at sunrise" --language en
```

## Output Location

Run outputs are written under:

```text
data/runs/{run_id}
```

Each run can contain prompts, workflow payloads, generated videos, extracted
frames, observations, evaluation reports, version diffs, traces, and export
files.

## Next Steps

- Configure real local providers in [Configuration](configuration.md).
- Review supported provider types in [Providers](providers.md).
- Understand the evaluation loop in [Evaluation](evaluation.md).
