import pytest
from backend.serp import LiveSerpClient, SerpError

class FakeResp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._payload = status, payload if payload is not None else {}
    def json(self):
        return self._payload

class FakeSession:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []
    def get(self, url, params=None, timeout=None):
        self.calls.append(params)
        return self.responses.pop(0)

def make(tmp_path, session, limit=40):
    return LiveSerpClient("KEY", tmp_path, ttl_hours=1, daily_limit=limit, session=session)

def test_second_identical_search_is_served_from_cache(tmp_path):
    sess = FakeSession(FakeResp(payload={"organic_results": [{"title": "a"}]}))
    c = make(tmp_path, sess)
    c.search("google", "web", q="acme"); c.search("google", "web", q="acme")
    assert len(sess.calls) == 1 and c.searches_made == 1 and c.cache_hits == 1
    assert c.trace[1]["cached"] is True

def test_api_key_is_sent_but_never_cached(tmp_path):
    sess = FakeSession(FakeResp(payload={"organic_results": [{"title": "a"}], "search_parameters": {"api_key": "KEY"}}))
    c = make(tmp_path, sess)
    c.search("google", "web", q="acme")
    assert sess.calls[0]["api_key"] == "KEY" and sess.calls[0]["gl"] == "in"
    assert all("KEY" not in f.read_text() for f in tmp_path.glob("*.json"))

def test_no_results_error_becomes_empty_not_failure(tmp_path):
    sess = FakeSession(FakeResp(payload={"error": "Google Maps hasn't returned any results for this query."}))
    data = make(tmp_path, sess).search("google_maps", "maps", q="nothing")
    assert data["organic_results"] == []

def test_invalid_key_and_rate_limit(tmp_path):
    with pytest.raises(SerpError, match="API key"):
        make(tmp_path, FakeSession(FakeResp(401, {"error": "Invalid API key"}))).search("google", "web", q="x")
    with pytest.raises(SerpError, match="rate limited"):
        make(tmp_path / "b", FakeSession(FakeResp(429, {}))).search("google", "web", q="y")

def test_daily_guard_stops_before_spending(tmp_path):
    sess = FakeSession(FakeResp(payload={"organic_results": [{}]}), FakeResp(payload={"organic_results": [{}]}))
    c = make(tmp_path, sess, limit=1)
    c.search("google", "web", q="one")
    with pytest.raises(SerpError, match="Daily search guard"):
        c.search("google", "web", q="two")
    assert len(sess.calls) == 1
