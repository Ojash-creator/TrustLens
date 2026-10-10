#!/usr/bin/env bash
# TrustLens setup for macOS / Linux.
# Run this from inside the trustlens folder:   bash setup.sh   (or ./setup.sh after chmod +x)
set -e

echo ""
echo "== TrustLens setup =="

if [ ! -f "run.py" ]; then
    echo "FAILED: run.py not found here. cd into the trustlens folder first, then run this script again."
    exit 1
fi

echo ""
echo "== Step 1: Creating virtual environment =="
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
if [ ! -d ".venv" ]; then
    echo "FAILED: .venv was not created. Is python3 installed? Try 'python3 --version'."
    exit 1
fi
echo "OK: .venv ready"

echo ""
echo "== Step 2: Activating virtual environment =="
source .venv/bin/activate

echo ""
echo "== Step 3: Installing requirements =="
pip install -r requirements.txt

echo ""
echo "== Step 4: SerpApi key =="
echo "Get a free key (250 searches/month) at https://serpapi.com/manage-api-key"
echo "Leave this blank and press Enter to run in Demo mode instead (no credits used)."
read -r -p "Paste your SerpApi key (or press Enter to skip): " key

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

if [ -n "$key" ]; then
    # portable in-place edit for both GNU and BSD/macOS sed
    sed -i.bak "s|^SERPAPI_KEY=.*|SERPAPI_KEY=$key|" .env && rm -f .env.bak
    echo "OK: key saved to .env. TrustLens will run in LIVE mode."
else
    echo "OK: no key entered. TrustLens will run in DEMO mode (recorded data, no credits used)."
    echo "You can add a key later: open .env in a text editor and set SERPAPI_KEY=..."
fi

echo ""
echo "== Step 5: Starting TrustLens =="
echo "Once you see 'Open http://localhost:5000', open that link in your browser."
echo "Press Ctrl+C here to stop the server."
echo ""
python run.py
