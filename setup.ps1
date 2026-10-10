# TrustLens setup for Windows PowerShell.
# Run this from inside the trustlens folder:   .\setup.ps1

Write-Host ""
Write-Host "== TrustLens setup ==" -ForegroundColor Cyan

if (-not (Test-Path "run.py")) {
    Write-Host "FAILED: run.py not found here. cd into the trustlens folder first, then run .\setup.ps1 again." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "== Step 1: Creating virtual environment ==" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
if (-not (Test-Path ".venv")) {
    Write-Host "FAILED: .venv was not created. Is Python installed and on PATH? Try 'python --version'." -ForegroundColor Red
    exit 1
}
Write-Host "OK: .venv ready" -ForegroundColor Green

Write-Host ""
Write-Host "== Step 2: Activating virtual environment ==" -ForegroundColor Cyan
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. .\.venv\Scripts\Activate.ps1

Write-Host ""
Write-Host "== Step 3: Installing requirements ==" -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host ""
Write-Host "== Step 4: SerpApi key ==" -ForegroundColor Cyan
Write-Host "Get a free key (250 searches/month) at https://serpapi.com/manage-api-key" -ForegroundColor Yellow
Write-Host "Leave this blank and press Enter to run in Demo mode instead (no credits used)." -ForegroundColor Yellow
$key = Read-Host "Paste your SerpApi key (or press Enter to skip)"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

if ($key -and $key.Trim() -ne "") {
    $envContent = Get-Content ".env" -Raw
    $envContent = $envContent -replace "(?m)^SERPAPI_KEY=.*$", "SERPAPI_KEY=$($key.Trim())"
    Set-Content ".env" $envContent -NoNewline
    Write-Host "OK: key saved to .env. TrustLens will run in LIVE mode." -ForegroundColor Green
} else {
    Write-Host "OK: no key entered. TrustLens will run in DEMO mode (recorded data, no credits used)." -ForegroundColor Yellow
    Write-Host "You can add a key later: open .env in Notepad and set SERPAPI_KEY=..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "== Step 5: Starting TrustLens ==" -ForegroundColor Cyan
Write-Host "Once you see 'Open http://localhost:5000', open that link in your browser." -ForegroundColor Yellow
Write-Host "Press Ctrl+C here to stop the server." -ForegroundColor Yellow
Write-Host ""
python run.py
