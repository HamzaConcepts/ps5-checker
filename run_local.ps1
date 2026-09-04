# PlayStation 5 Stock Bot PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    Starting PlayStation 5 Stock Monitor Bot" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt --quiet

Write-Host "Launching PS5 Stock Monitor..." -ForegroundColor Green
python main.py
