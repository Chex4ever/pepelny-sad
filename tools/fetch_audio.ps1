# Download and prepare game audio assets (CC0 / Public Domain).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
python tools/prepare_audio.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Audio assets ready in assets/audio/"
