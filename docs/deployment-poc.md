# POC Deployment Notes

ShotForge is currently a local-first POC. It is designed to run on a laptop for review, demos, and solution walkthroughs.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

Copy the example environment file if you want explicit local paths:

```bash
copy .env.example .env
```

The default config writes runtime data under `data/`, which is ignored by git.

## CLI Demo

```bash
shotforge design "A neon train crossing a desert at sunrise" --language en
```

Windows one-command demo:

```powershell
.\scripts\demo.ps1 -Language en
```

Inspect the generated harness evidence:

```bash
shotforge audit data/runs/{run_id}/package.json
```

Inspect available agents, providers, playbooks, exports, and routes:

```bash
shotforge capabilities
```

Check local configuration and storage paths:

```bash
shotforge doctor
```

## Web Demo

```bash
python -m uvicorn shotforge.app.web.app:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Useful API routes:

```text
POST /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/harness
GET /api/health
GET /api/runs/{run_id}/export/{format}
```

Supported export formats include:

- `json`
- `csv`
- `markdown`
- `manifest`
- `trace`
- `run_summary`
- `evaluation_csv`

## Storage Layout

```text
data/
  runs/{run_id}/
    package.json
    package.csv
    package.md
    manifest.json
    trace.json
    run_summary.md
    evaluation.csv
  versions/{project_id}/
  knowledge_base.json
  memory.jsonl
```

## Production Boundary

Before a real customer pilot, the following should be added:

- auth and tenant/project isolation
- production database or object storage
- official MCP transport if external tools are required
- stronger sandbox isolation, such as container execution
- real LLM/video provider credentials and quota controls
- observability, health checks, and deployment profiles
- customer-specific playbook overlays or RAG-backed knowledge retrieval

The current value of the POC is that these boundaries are explicit in state, readiness reports, docs, and audit exports.
