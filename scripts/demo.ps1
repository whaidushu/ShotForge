param(
    [string]$Idea = "A neon train crossing a desert at sunrise",
    [ValidateSet("zh", "en")]
    [string]$Language = "en",
    [int]$Duration = 24
)

$ErrorActionPreference = "Stop"

Write-Host "Running ShotForge design demo..." -ForegroundColor Cyan
python -m shotforge design "$Idea" --language $Language --duration $Duration

$package = Get-ChildItem -Path "data\runs" -Filter "package.json" -Recurse |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $package) {
    throw "No package.json found under data\runs."
}

Write-Host ""
Write-Host "Latest package:" $package.FullName -ForegroundColor Cyan
Write-Host ""
Write-Host "Harness audit:" -ForegroundColor Cyan
python -m shotforge audit $package.FullName

Write-Host ""
Write-Host "Open the Web demo with:" -ForegroundColor Cyan
Write-Host "python -m uvicorn shotforge.app.web.app:app --reload --host 127.0.0.1 --port 8000"
