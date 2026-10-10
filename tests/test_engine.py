import pytest
from backend.app import create_app
from backend.demo_data import SAMPLES
from backend.engine import run_check, clean_inputs
from backend.matching import domain_matches_company, is_match, mentions, registrable, similarity
from backend.serp import DemoSerpClient
from backend.signals import analyze_web, price_signal
from backend.textflags import analyze_message, analyze_url

@pytest.mark.parametrize("sample", SAMPLES, ids=[s["id"] for s in SAMPLES])
def test_sample_verdicts(sample):
    report = run_check(sample["mode"], sample["inputs"], DemoSerpClient(sample["responses"]), source="demo")
    assert report["verdict"]["level"] == sample["expected"]
    assert 3 <= report["score"] <= 97
    assert report["trace"]

def test_scores_are_ordered_by_risk():
    scores = {}
    for s in SAMPLES:
        scores[s["id"]] = run_check(s["mode"], s["inputs"], DemoSerpClient(s["responses"]), source="demo")["score"]
    assert scores["job-fake-wfh"] < scores["job-bpo-mixed"] < scores["job-legit-analyst"]
    assert scores["shop-fake-headphones"] < scores["shop-legit-headphones"]

def test_absence_alone_never_says_high_risk():
    report = run_check("job", {"name": "Totally Unknown Traders", "role": "Clerk"}, DemoSerpClient(None), source="demo")
    assert report["verdict"]["level"] == "insufficient"
    assert report["notes"]

def test_message_alone_can_trigger_high_risk():
    text = "Pay a registration fee of Rs. 999 to confirm your seat. No interview."
    report = run_check("job", {"name": "Unknown Co", "message": text}, DemoSerpClient(None), source="demo")
    assert report["verdict"]["level"] == "high_risk"

def test_followup_search_only_when_first_pass_finds_smoke():
    fake = next(s for s in SAMPLES if s["id"] == "job-fake-wfh")
    legit = next(s for s in SAMPLES if s["id"] == "job-legit-analyst")
    fake_r = run_check("job", fake["inputs"], DemoSerpClient(fake["responses"]), source="demo")
    legit_r = run_check("job", legit["inputs"], DemoSerpClient(legit["responses"]), source="demo")
    assert any(t["purpose"] == "followup" for t in fake_r["trace"])
    assert not any(t["purpose"] == "followup" for t in legit_r["trace"])

def test_negated_scam_mentions_do_not_count():
    results = [{"title": "Kestrel Analytics legit?", "link": "https://x.in/a", "snippet": "Kestrel Analytics is not a scam. No fraud reported."}]
    assert analyze_web("Kestrel Analytics", results)["strong"] == 0

def test_plural_scam_words_are_caught():
    results = [{"title": "Scammers use Acme Traders name", "link": "https://x.in/a", "snippet": "Acme Traders is cited."}]
    assert analyze_web("Acme Traders", results)["strong"] == 1

def test_price_bands():
    data = {"shopping_results": [{"source": f"S{i}", "extracted_price": p} for i, p in enumerate([100, 105, 110, 95, 100])]}
    assert price_signal(30, data)[0]["status"] == "fail"
    assert price_signal(70, data)[0]["status"] == "warn"
    assert price_signal(101, data)[0]["status"] == "pass"
    assert price_signal(None, data)[0]["status"] == "unknown"

def test_message_rules():
    ok = analyze_message("Please bring your ID on Friday. No fee is charged at any stage.", "job")
    assert ok["flags"] == []
    bad = analyze_message("Pay refundable registration fee of Rs 2,000 on WhatsApp only", "job")
    ids = {f["id"] for f in bad["flags"]}
    assert {"fee_request", "chat_only"} <= ids and bad["critical"]

def test_url_rules():
    assert analyze_url("https://megadealz-official-outlet.top/x")["penalty"] >= 14
    assert analyze_url("https://amazon-deals-india.com")["flags"]
    assert analyze_url("https://www.urbancart.in/p/1")["clean"]

def test_matching():
    assert is_match("SwiftHire Global Services", "Swift Hire Global Services")
    assert not is_match("SwiftHire Global Services", "Swift Print Solutions")
    assert similarity("Kestrel Analytics Pvt Ltd", "Kestrel Analytics") == 1.0
    assert mentions("Beware of Swift Hire scam", "SwiftHire Global Services")
    assert registrable("careers.kestrel.co.in") == "kestrel.co.in"
    assert domain_matches_company("kestrelanalytics.in", "Kestrel Analytics Pvt Ltd")

def test_input_validation():
    with pytest.raises(ValueError):
        clean_inputs("job", {"name": ""})
    with pytest.raises(ValueError):
        clean_inputs("shop", {})
    assert clean_inputs("shop", {"url": "https://www.urbancart.in/p/1"})["name"] == "Urbancart"

def test_api_roundtrip(monkeypatch):
    monkeypatch.setattr("backend.config.Config.SERPAPI_KEY", "")
    client = create_app().test_client()
    assert client.get("/api/health").get_json()["mode"] == "demo"
    samples = client.get("/api/samples").get_json()
    assert len(samples) == len(SAMPLES) and "responses" not in samples[0]
    s = samples[0]
    r = client.post("/api/analyze", json={"mode": s["mode"], "inputs": s["inputs"], "sample_id": s["id"]})
    assert r.status_code == 200 and r.get_json()["verdict"]["level"] == "high_risk"
    assert client.post("/api/analyze", json={"mode": "job", "inputs": {}}).status_code == 400
    assert client.get("/").status_code in (200, 404)
