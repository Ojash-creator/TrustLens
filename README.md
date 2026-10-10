# TrustLens

**Check before you trust.** Paste a job offer, a shop link or a business name, and TrustLens
searches live Google data through [SerpApi](https://serpapi.com) to tell you whether it looks
legitimate, and shows the evidence behind every verdict.

Built for the **SerpApi India Hackathon 2026**.

---

## Quickest start: one script does everything

After unzipping, open a terminal **inside the `trustlens` folder** and run:

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

**macOS / Linux:**
```bash
bash setup.sh
```

This single script will:
1. Create a Python virtual environment (`.venv`)
2. Install the dependencies
3. **Ask you to paste your SerpApi key** (or just press Enter to skip and run in Demo mode)
4. Start the app at `http://localhost:5000`

If PowerShell blocks the script, it already runs `Set-ExecutionPolicy -Scope Process Bypass` for you, so just try `.\setup.ps1` again. If it still refuses to run at all, see "Manual setup" below.

**No Python at all?** Open `dist/trustlens-demo.html` directly in any browser — a single self-contained file with all eight recorded demo cases pre-computed. No install needed.

---

## Where to get a SerpApi key

1. Sign up free at **https://serpapi.com/users/sign_up**
2. Copy your key from **https://serpapi.com/manage-api-key**
3. Paste it when `setup.ps1` / `setup.sh` asks for it

The free plan gives **250 searches/month**. Each check uses about 4-6 searches. TrustLens protects your quota:
- every response is cached on disk for 24 hours
- a daily guard (`TRUSTLENS_DAILY_SEARCH_LIMIT`, default 40) stops before you burn the month
- the top-right pill shows how many searches you've used today
- your key is never written to the cache or sent to the browser

You can run `setup.ps1` / `setup.sh` again any time to add or change the key, or edit `.env` directly.

---

## Manual setup (if you'd rather not use the script)

**Windows (PowerShell):**
```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env          # paste your key after SERPAPI_KEY=, save, close
python run.py
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env              # paste your key after SERPAPI_KEY=, save, exit
python run.py
```

Either way, open **http://localhost:5000** once you see `Open http://localhost:5000` printed.

---

## How it works

```
 input (offer / shop / business)
        |
        v
  planner picks the searches that fit the case, adds follow-ups when results look suspicious
        |
        +-- google_maps          does the business exist? rating? contact details?
        +-- google_maps_reviews  what do the lowest-rated customers say?
        +-- google_jobs          is the role advertised by this company?
        +-- google_shopping      price vs. the market median, is the seller known?
        +-- google (web)         scam / fraud / complaint pages -- follow-up on forums if smoke found
        +-- google_news          reputable coverage, good or bad
        |
        v
  Signals -> Score (start 50, fixed weights) -> Verdict + reasons + evidence + next steps
```

Every check starts at **50**. Each signal adds or subtracts a fixed number of points, visible in
the report's waterfall chart (source: `WEIGHTS` in `backend/signals.py`).

- **72+** looks legitimate, **45-71** proceed with caution, **below 45** high risk.
- **Critical findings** (a fee request, a bait price far below market, repeated scam reports) cap the verdict at *caution* even
  if everything else looks good, and force *high risk* when the score is below 60.
- **Absence is not evidence.** A low score caused only by something *missing* (no Maps listing, no job posting) becomes
  *Not enough evidence*, never *High risk*.
- **Evidence coverage** shows how much of the picture TrustLens could see. Under 40% also means *Not enough evidence*.

### The "message X-ray"

Paste the WhatsApp text and TrustLens highlights every phrase that matches a known scam pattern
(registration fees, "no interview", Aadhaar requests, personal-UPI payments, "guaranteed selection"...)
with a plain-English reason for each. These rules are in `backend/textflags.py` and cost no credits.

---

## Project layout

```
setup.ps1 / setup.sh     one-command setup: venv, install, ask for API key, launch
backend/
  app.py         Flask routes: /api/health, /api/samples, /api/analyze
  engine.py      planner, adaptive follow-ups, scoring, verdict, next steps
  signals.py     turns raw SerpApi JSON into scored, explained findings (+ WEIGHTS table)
  textflags.py   message and URL red-flag rules (offline, no credits)
  matching.py    company-name and domain matching
  serp.py        LiveSerpClient (cache, daily budget, trace) and DemoSerpClient
  demo_data.py   8 fictional recorded cases in SerpApi's response shapes
  llm.py         optional Claude summary (never touches the score)
frontend/        index.html, css/styles.css, js/app.js (vanilla, no build step)
scripts/build_static_demo.py   rebuilds dist/trustlens-demo.html
tests/           25 tests: verdicts, scoring rules, matching, live-client failure handling
docs/            SUBMISSION.md, DEMO_SCRIPT.md
```

## Tests

```bash
pytest -q          # 25 tests, no network, no credits
```

## Rebuild the offline demo

```bash
python scripts/build_static_demo.py
```

## Security and privacy notes

- All text scraped from the web is HTML-escaped before display.
- External links open with `rel="noopener noreferrer nofollow"`.
- Check history is stored only in your browser's `localStorage`.
- Your `.env` file (containing your key) is excluded by `.gitignore` and is never committed.
- Verdicts are advisory summaries of public search evidence, not a legal finding about any business.

## Credits

Search data by [SerpApi](https://serpapi.com). Development assisted by Claude (Anthropic). All demo companies, stores and people are fictional.
