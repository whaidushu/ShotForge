# API Reference

This page lists the primary local API and CLI entrypoints. Run the Web app first:

```powershell
shotforge web --reload
```

## Health And Capabilities

```text
GET /api/health
GET /api/capabilities
```

## Runs

```text
POST /api/runs
GET /api/runs
GET /api/runs/{run_id}
GET /api/runs/{run_id}/status
GET /api/runs/{run_id}/workbench
GET /api/runs/{run_id}/generation-artifacts
GET /api/runs/{run_id}/versions
GET /api/runs/{run_id}/readiness
```

## Exports

```text
GET /api/runs/{run_id}/export/json
GET /api/runs/{run_id}/export/csv
GET /api/runs/{run_id}/export/markdown
GET /api/runs/{run_id}/export/evaluation_csv
```

## Providers

```text
GET /api/provider-profiles
POST /api/provider-profiles
GET /api/observer-providers
POST /api/preflight
GET /api/comfyui/workflows
```

## CLI

```powershell
shotforge design "idea" --language en
shotforge full-loop "idea" --language en --redesign --max-iterations 2
shotforge doctor --deep
shotforge audit data/runs/{run_id}/package.json
shotforge web --reload
```
