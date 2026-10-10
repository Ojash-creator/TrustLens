from __future__ import annotations
import re, statistics
from typing import Any
from urllib.parse import quote
from .matching import core_tokens, domain_matches_company, host_of, is_match, mentions, registrable, similarity
from .textflags import BRANDS, analyze_message, analyze_url, is_freemail

WEIGHTS: dict[str, dict[str, tuple[int, int]]] = {
    "job": {"maps_presence": (12, 10), "maps_reputation": (8, 10), "job_posting": (16, 6),
            "recruiter": (10, 16), "message": (4, 35), "web": (10, 24), "news": (6, 16), "reviews": (6, 12)},
    "shop": {"price": (10, 26), "seller": (14, 4), "maps_presence": (8, 2), "maps_reputation": (8, 10),
             "url": (6, 24), "message": (4, 35), "web": (10, 24), "news": (5, 16)},
    "local": {"maps_presence": (16, 18), "maps_reputation": (14, 14), "reviews": (6, 16), "contact": (6, 6),
              "message": (4, 35), "web": (10, 24), "news": (5, 16)},
}

WEB_STRONG = ("scam", "scammer", "fraud", "fraudulent", "fake", "cheat", "cheated", "cheating", "ponzi",
              "blacklisted", "not genuine", "beware", "duped", "phishing", "looted", "con artist")
WEB_WEAK = ("complaint", "complaints", "refund", "not received", "harass", "poor service", "worst", "delayed salary",
            "salary delay", "deducted", "no response")
NEGATION = re.compile(r"\b(not|no|isn'?t|is not|never|without)\s+(a\s+|any\s+)?(scam|fraud|fake)\b", re.I)
NEWS_NEG = ("fraud", "scam", "arrested", "raid", "ponzi", "cheating", "fir ", "blacklist", "duped", "probe",
            "penalty", "refund", "consumer commission", "consumer court", "shut down", "illegal")
NEWS_POS = ("raises", "funding", "series ", "opens", "expands", "expansion", "hires", "hiring", "ipo", "partnership",
            "launches", "acquires", "wins", "award", "inaugurates", "milestone")
REVIEW_TERMS = ("scam", "fraud", "cheat", "cheated", "fake", "refund", "waste of money", "advance", "harass",
                "unprofessional", "not return", "misbehav", "no response", "false promise", "misled", "overcharg")
HOST_KINDS = (("complaint", "Complaint site"), ("scam", "Scam checker"), ("reddit", "Forum"), ("quora", "Forum"),
              ("forum", "Forum"), ("review", "Review site"), ("glassdoor", "Review site"),
              ("ambitionbox", "Review site"), ("trustpilot", "Review site"), ("mouthshut", "Review site"),
              ("linkedin", "Professional network"), ("naukri", "Job portal"), ("indeed", "Job portal"),
              ("news", "News"), ("times", "News"), ("hindu", "News"), ("express", "News"))

def signal(id_, category, title, status, points, finding, detail="", evidence=None, weight=0,
           engines=None, optional=False, critical=False, absence=False):
    return {"id": id_, "category": category, "title": title, "status": status, "points": int(points),
            "finding": finding, "detail": detail, "evidence": evidence or [], "weight": int(weight),
            "engines": engines or [], "optional": optional, "critical": critical, "absence": absence}

def unknown(id_, category, title, finding, detail, weight, engines=None, optional=False):
    return signal(id_, category, title, "unknown", 0, finding, detail, weight=weight, engines=engines, optional=optional)

def _w(mode, key):
    return WEIGHTS[mode][key]

def _num(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.]", "", str(value).replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def _ev(label, value, url=None):
    row = {"label": label, "value": str(value)}
    if url:
        row["url"] = url
    return row

def _place_candidates(data):
    cands = []
    pr = data.get("place_results")
    if isinstance(pr, dict) and pr.get("title"):
        cands.append(pr)
    lr = data.get("local_results")
    if isinstance(lr, dict):
        lr = lr.get("places")
    for r in lr or []:
        if isinstance(r, dict) and r.get("title"):
            cands.append(r)
    return cands

def place_view(p, score):
    gps = p.get("gps_coordinates") or {}
    types = p.get("types") or []
    query = quote(f"{p.get('title', '')} {p.get('address', '')}".strip())
    link = f"https://www.google.com/maps/search/?api=1&query={query}"
    if p.get("place_id"):
        link += f"&query_place_id={quote(str(p['place_id']))}"
    return {"title": p.get("title"), "rating": _num(p.get("rating")), "reviews": int(_num(p.get("reviews")) or 0),
            "address": p.get("address"), "phone": p.get("phone"), "website": p.get("website"),
            "type": p.get("type") or (types[0] if types else None), "data_id": p.get("data_id"),
            "lat": gps.get("latitude"), "lng": gps.get("longitude"), "open_state": p.get("open_state"),
            "match": round(score, 2), "link": link}

def pick_place(data, name):
    scored = sorted(((similarity(name, c["title"]), c) for c in _place_candidates(data)), key=lambda x: -x[0])
    views = [place_view(c, s) for s, c in scored[:3]]
    if scored and scored[0][0] >= 0.75:
        return place_view(scored[0][1], scored[0][0]), views
    return None, views

def maps_presence_signal(mode, name, place, near):
    pos, neg = _w(mode, "maps_presence")
    if place:
        ev = [_ev("Listed as", place["title"]), _ev("Address", place["address"] or "not shown"),
              _ev("Category", place["type"] or "not shown"), _ev("Open on Google Maps", "view listing", place["link"])]
        return signal("maps_presence", "identity", "Business footprint", "pass", pos,
                      f"Found \u201c{place['title']}\u201d on Google Maps",
                      "A real, findable location or business profile is hard to fake at scale. "
                      "It is one of the strongest identity signals available in public search.",
                      ev, max(pos, neg), ["google_maps"])
    ev = [_ev("Closest listing", f"{v['title']} (match {int(v['match'] * 100)}%)") for v in near[:2]]
    label = {"job": "This company has no matching Google Maps listing",
             "shop": "No physical or business listing found for this store",
             "local": "No Google Maps listing matches this name"}[mode]
    why = {"job": "Real employers usually have an office or business profile. New start-ups can be an exception, so verify through other channels.",
           "shop": "Many honest online stores have no shop front, so this is only a light concern.",
           "local": "A local business that cannot be found on Google Maps is a serious red flag."}[mode]
    status = "fail" if neg >= 10 else "warn"
    return signal("maps_presence", "identity", "Business footprint", status, -neg, label, why, ev,
                  max(pos, neg), ["google_maps"], absence=True)

def maps_reputation_signal(mode, place):
    pos, neg = _w(mode, "maps_reputation")
    rating, n = place.get("rating"), place.get("reviews") or 0
    ev = [_ev("Rating", f"{rating} out of 5" if rating else "no rating"), _ev("Number of reviews", f"{n:,}")]
    full_n = 50 if mode == "local" else 25
    if rating is None or n < 5:
        return signal("maps_reputation", "reputation", "Public reviews", "warn", -2 if mode != "local" else -4,
                      f"Only {n} review{'s' if n != 1 else ''} on Google Maps",
                      "A very short review history means there is little public evidence either way.", ev, max(pos, neg), ["google_maps"])
    if rating >= 4.0 and n >= full_n:
        return signal("maps_reputation", "reputation", "Public reviews", "pass", pos,
                      f"{rating}\u2605 from {n:,} reviews",
                      "A high rating backed by many independent reviews is expensive for fraudsters to imitate.", ev, max(pos, neg), ["google_maps"])
    if rating >= 3.5:
        pts = max(1, round(pos * 0.25))
        return signal("maps_reputation", "reputation", "Public reviews", "info", pts,
                      f"Mixed reputation: {rating}\u2605 from {n:,} reviews",
                      "Not alarming, but not strongly reassuring either. Read the recent reviews before deciding.", ev, max(pos, neg), ["google_maps"])
    if rating >= 3.0:
        return signal("maps_reputation", "reputation", "Public reviews", "warn", -4,
                      f"Below-average rating: {rating}\u2605 from {n:,} reviews",
                      "Customers are noticeably unhappy. Check what the complaints are about.", ev, max(pos, neg), ["google_maps"])
    if n >= 10:
        return signal("maps_reputation", "reputation", "Public reviews", "fail", -neg,
                      f"Poor rating: {rating}\u2605 from {n:,} reviews",
                      "A low score across many reviews is a strong warning sign.", ev, max(pos, neg), ["google_maps"])
    return signal("maps_reputation", "reputation", "Public reviews", "warn", -5,
                  f"Low rating ({rating}\u2605) but from only {n} reviews",
                  "Too few reviews to be sure, but the early signal is negative.", ev, max(pos, neg), ["google_maps"])

def contact_signal(mode, place):
    pos, neg = _w(mode, "contact")
    have = {"phone": bool(place.get("phone")), "website": bool(place.get("website")), "address": bool(place.get("address"))}
    n = sum(have.values())
    ev = [_ev(k.title(), place.get(k) or "missing") for k in ("phone", "website", "address")]
    if n == 3:
        return signal("contact", "identity", "Contact details", "pass", pos, "Phone, website and address are all published",
                      "Traceable contact details make it possible to hold a business accountable.", ev, pos, ["google_maps"])
    if n == 2:
        miss = [k for k, v in have.items() if not v][0]
        return signal("contact", "identity", "Contact details", "warn", -2, f"No {miss} on the listing",
                      "One contact channel is missing. Ask for it before paying anything.", ev, pos, ["google_maps"])
    return signal("contact", "identity", "Contact details", "fail", -neg, "Most contact details are missing",
                  "Businesses that hide phone, website and address are hard to trace if something goes wrong.", ev, pos, ["google_maps"])

def job_posting_signal(company, role, data):
    pos, neg = _w("job", "job_posting")
    jobs = [j for j in (data.get("jobs_results") or []) if isinstance(j, dict)]
    views = []
    for j in jobs[:6]:
        opts = j.get("apply_options") or []
        views.append({"title": j.get("title"), "company": j.get("company_name"), "location": j.get("location"),
                      "via": j.get("via"), "posted": (j.get("detected_extensions") or {}).get("posted_at"),
                      "link": (opts[0].get("link") if opts else None) or j.get("share_link"),
                      "from_company": is_match(company, j.get("company_name", ""))})
    hits = [v for v in views if v["from_company"]]
    if hits:
        ev = [_ev(f"{v['company']} via {v['via'] or 'Google Jobs'}", v["title"], v["link"]) for v in hits[:3]]
        return signal("job_posting", "market", "Listed on Google Jobs", "pass", pos,
                      f"{len(hits)} live posting{'s' if len(hits) > 1 else ''} from this company on Google Jobs",
                      "Genuine employers post openings on public job boards. Fake offers usually only exist in a chat message.",
                      ev, pos, ["google_jobs"]), views
    if views:
        names = ", ".join(sorted({v["company"] or "unknown" for v in views[:4]}))
        return signal("job_posting", "market", "Listed on Google Jobs", "warn", -4,
                      "Similar roles exist, but none are posted by this company",
                      f"Google Jobs shows the role under other names ({names}). It could be a staffing agency "
                      "or a different company using the same title. Ask who the actual employer is.",
                      [_ev(f"{v['company']} via {v['via'] or 'board'}", v["title"], v["link"]) for v in views[:3]],
                      pos, ["google_jobs"], absence=True), views
    return signal("job_posting", "market", "Listed on Google Jobs", "warn", -neg,
                  "No public posting for this role was found",
                  "Not every job is advertised, but an offer that exists only in a private message deserves extra checking.",
                  [], pos, ["google_jobs"], absence=True), views

def _kind(host):
    for key, label in HOST_KINDS:
        if key in host:
            return label
    return "Website"

def analyze_web(name, results, domain=""):
    items, strong, weak, relevant, official = [], 0, 0, 0, 0
    for r in results:
        if not isinstance(r, dict):
            continue
        title, snippet, link = r.get("title", "") or "", r.get("snippet", "") or "", r.get("link", "") or ""
        host = host_of(link)
        text = f"{title}. {snippet}"
        is_official = bool(domain) and registrable(host) == registrable(domain)
        rel = mentions(text, name) or is_official or (bool(domain) and domain in link)
        low = text.lower()
        strong_terms = [t for t in WEB_STRONG if re.search(rf"\b{re.escape(t)}s?\b", low)] if rel else []
        if strong_terms and NEGATION.search(text):
            strong_terms = []
        weak_terms = [t for t in WEB_WEAK if t in low] if rel and not strong_terms else []
        flag = "strong" if strong_terms else "weak" if weak_terms else "none"
        relevant += rel; strong += flag == "strong"; weak += flag == "weak"; official += is_official
        items.append({"title": title, "link": link, "host": host, "snippet": snippet, "kind": _kind(host),
                      "relevant": rel, "official": is_official, "flag": flag,
                      "terms": strong_terms or weak_terms, "date": r.get("date")})
    order = {"strong": 0, "weak": 1, "none": 2}
    items.sort(key=lambda i: (order[i["flag"]], not i["relevant"]))
    return {"items": items[:8], "strong": strong, "weak": weak, "relevant": relevant, "official": official, "total": len(items)}

def web_signal(name, an, followup):
    pos, neg = 10, 24
    top = [i for i in an["items"] if i["flag"] == "strong"][:3] or [i for i in an["items"] if i["flag"] == "weak"][:3]
    ev = [_ev(f"{i['kind']}: {i['host']}", i["title"], i["link"]) for i in top]
    eng = ["google"]
    fu = " A follow-up search on forums and consumer-complaint pages confirmed it." if followup else ""
    if an["strong"] >= 2:
        return signal("web", "coverage", "Scam and complaint reports", "fail", -neg,
                      f"{an['strong']} pages link \u201c{name}\u201d to scam or fraud reports",
                      "Independent pages describe the same pattern. Multiple unrelated reports are a strong warning." + fu,
                      ev, neg, eng, critical=True)
    if an["strong"] == 1:
        return signal("web", "coverage", "Scam and complaint reports", "warn", -12,
                      f"1 page links \u201c{name}\u201d to scam or fraud reports",
                      "A single report may be a disgruntled customer or a real warning. Open it and judge the details." + fu,
                      ev, neg, eng)
    if an["weak"] >= 2:
        return signal("web", "coverage", "Scam and complaint reports", "warn", -5,
                      f"{an['weak']} pages mention complaints or refund problems",
                      "No outright fraud claims, but a repeated pattern of complaints is worth reading.", ev, neg, eng)
    if an["relevant"] >= 3:
        return signal("web", "coverage", "Scam and complaint reports", "pass", pos,
                      f"{an['relevant']} relevant pages found, none report scams",
                      "The name shows up across the web with no scam or fraud warnings attached.",
                      [_ev(f"{i['kind']}: {i['host']}", i["title"], i["link"]) for i in an["items"] if i["relevant"]][:3], neg, eng)
    return unknown("web", "coverage", "Scam and complaint reports",
                   "Too little web coverage to judge",
                   "Fewer than three relevant pages mention this name. Absence of complaints is not proof of safety.", neg, eng)

def analyze_news(name, data):
    raw = []
    for r in data.get("news_results") or []:
        if isinstance(r, dict):
            raw.append(r)
            raw.extend(s for s in (r.get("stories") or []) if isinstance(s, dict))
    items, neg, pos = [], 0, 0
    for r in raw:
        title, snippet = r.get("title", "") or "", r.get("snippet", "") or ""
        if not mentions(f"{title}. {snippet}", name):
            continue
        low = f" {title.lower()} {snippet.lower()} "
        n_terms = [t for t in NEWS_NEG if t in low]
        p_terms = [t for t in NEWS_POS if t in low]
        tone = "negative" if n_terms else "positive" if p_terms else "neutral"
        neg += tone == "negative"; pos += tone == "positive"
        src = r.get("source")
        src = src.get("name") if isinstance(src, dict) else src
        items.append({"title": title, "link": r.get("link"), "source": src, "date": r.get("date"),
                      "snippet": snippet, "tone": tone, "terms": n_terms or p_terms})
    return {"items": items[:6], "neg": neg, "pos": pos}

def news_signal(mode, name, an):
    pos_w, neg_w = _w(mode, "news")
    ev = [_ev(f"{i['source'] or 'News'}, {i['date'] or ''}".strip(", "), i["title"], i["link"]) for i in an["items"][:3]]
    if an["neg"] >= 2:
        return signal("news", "coverage", "News coverage", "fail", -neg_w, f"{an['neg']} negative news stories",
                      "Headlines mention fraud, penalties, raids or similar problems.", ev, neg_w, ["google_news"])
    if an["neg"] == 1:
        return signal("news", "coverage", "News coverage", "warn", -10, "1 negative news story",
                      "Read the story to see whether it applies to what you are being offered.", ev, neg_w, ["google_news"])
    if an["pos"] >= 2:
        return signal("news", "coverage", "News coverage", "pass", pos_w, f"{an['pos']} positive business stories",
                      "Funding, expansion or hiring news from reputable outlets suggests a real, operating organisation.",
                      ev, neg_w, ["google_news"], optional=True)
    if an["pos"] == 1:
        return signal("news", "coverage", "News coverage", "pass", max(2, pos_w // 2), "1 positive business story",
                      "A news mention is a mild sign of a real, operating organisation.", ev, neg_w, ["google_news"], optional=True)
    return unknown("news", "coverage", "News coverage", "No news coverage found",
                   "Small businesses often have none, so this neither helps nor hurts.", neg_w, ["google_news"], optional=True)

def recruiter_signal(company, email, website):
    pos, neg = _w("job", "recruiter")
    if not email:
        return unknown("recruiter", "behaviour", "Recruiter e-mail", "No recruiter e-mail provided",
                       "Add the address the offer came from. The domain says a lot about who is really writing.", neg, optional=True)
    domain = email.split("@", 1)[1].lower() if "@" in email else host_of(email)
    reg = registrable(domain)
    ev = [_ev("Sender domain", domain)]
    if website:
        ev.append(_ev("Company website on Google Maps", host_of(website)))
    for brand, official in BRANDS.items():
        if brand in reg.split(".")[0] and reg not in official and brand != "google":
            return signal("recruiter", "behaviour", "Recruiter e-mail", "fail", -neg,
                          f"Sender domain imitates \u201c{brand}\u201d",
                          "Scammers register look-alike domains of famous employers. This one is not that employer's real domain.",
                          ev, neg, [], critical=True)
    if is_freemail(domain):
        return signal("recruiter", "behaviour", "Recruiter e-mail", "fail", -10,
                      f"Recruiter uses a free e-mail ({domain})",
                      "Established companies hire from their own domain. Free mail accounts cost nothing to create.",
                      ev, neg, [])
    if website and registrable(host_of(website)) == reg:
        return signal("recruiter", "behaviour", "Recruiter e-mail", "pass", pos,
                      "Sender domain matches the company's official website",
                      "The e-mail comes from the same domain as the business listed on Google Maps.", ev, neg, [])
    if domain_matches_company(domain, company):
        return signal("recruiter", "behaviour", "Recruiter e-mail", "pass", max(4, pos // 2),
                      "Sender domain resembles the company name",
                      "It looks consistent with the company name, but could not be confirmed against an official website.", ev, neg, [])
    return signal("recruiter", "behaviour", "Recruiter e-mail", "warn", -8,
                  "Sender domain does not match the company",
                  "The address does not relate to the company name or its website. Ask the recruiter to write from an official address.",
                  ev, neg, [])

def _shopping_items(data):
    out = []
    for r in data.get("shopping_results") or []:
        if not isinstance(r, dict):
            continue
        price = _num(r.get("extracted_price")) or _num(r.get("price"))
        if price and price > 0:
            out.append({"seller": r.get("source") or r.get("seller") or "Unknown", "price": price,
                        "title": r.get("title"), "link": r.get("product_link") or r.get("link")})
    return sorted(out, key=lambda x: x["price"])

def price_signal(listed, data):
    pos, neg = _w("shop", "price")
    items = _shopping_items(data)
    if listed is None:
        return unknown("price", "market", "Price against the market", "No listed price provided",
                       "Enter the price you were shown to compare it with what Google Shopping sellers charge.", neg,
                       ["google_shopping"], optional=True), None
    if len(items) < 3:
        return unknown("price", "market", "Price against the market", "Not enough comparable listings",
                       "Google Shopping returned fewer than three priced results for this product.", neg, ["google_shopping"]), None
    prices = [i["price"] for i in items]
    med = statistics.median(prices)
    q1, q3 = statistics.quantiles(prices, n=4)[0], statistics.quantiles(prices, n=4)[2]
    ratio = listed / med
    pct = round(abs(1 - ratio) * 100)
    panel = {"listed": listed, "median": med, "min": min(prices), "max": max(prices), "q1": q1, "q3": q3,
             "ratio": round(ratio, 2), "items": items[:12]}
    ev = [_ev("Listed price", f"\u20b9{listed:,.0f}"), _ev("Market median", f"\u20b9{med:,.0f}"),
          _ev("Range on Google Shopping", f"\u20b9{min(prices):,.0f} to \u20b9{max(prices):,.0f}"), _ev("Sellers compared", len(items))]
    if ratio < 0.4:
        return signal("price", "market", "Price against the market", "fail", -neg,
                      f"{pct}% below the market median",
                      "Genuine sellers cannot sustain prices this far below everyone else. A price this low is bait.",
                      ev, neg, ["google_shopping"], critical=True), panel
    if ratio < 0.6:
        return signal("price", "market", "Price against the market", "fail", -16,
                      f"{pct}% below the market median",
                      "Much cheaper than every comparable seller. Very likely a bait price or a counterfeit.", ev, neg, ["google_shopping"]), panel
    if ratio < 0.8:
        return signal("price", "market", "Price against the market", "warn", -3,
                      f"{pct}% cheaper than the market median",
                      "A good deal is possible, but confirm the seller and the exact model before paying.", ev, neg, ["google_shopping"]), panel
    if ratio <= 1.3:
        return signal("price", "market", "Price against the market", "pass", pos,
                      "Price is in line with the market",
                      "The listed price sits inside the range charged by comparable sellers.", ev, neg, ["google_shopping"]), panel
    return signal("price", "market", "Price against the market", "info", 0,
                  f"{pct}% above the market median",
                  "Not a fraud signal, but you may find the same product cheaper elsewhere.", ev, neg, ["google_shopping"]), panel

def seller_signal(store, data):
    pos, neg = _w("shop", "seller")
    items = _shopping_items(data)
    if not store:
        return unknown("seller", "market", "Known seller", "No store name provided",
                       "Enter the store name to check whether Google Shopping knows it.", pos, ["google_shopping"], optional=True)
    hits = [i for i in items if is_match(store, i["seller"])]
    if hits:
        return signal("seller", "market", "Known seller", "pass", pos,
                      f"\u201c{hits[0]['seller']}\u201d is a listed Google Shopping seller",
                      "The store appears among sellers that Google itself lists for this product.",
                      [_ev(h["seller"], f"\u20b9{h['price']:,.0f}", h["link"]) for h in hits[:2]], pos, ["google_shopping"])
    if len(items) >= 5:
        return signal("seller", "market", "Known seller", "warn", -neg,
                      f"Not among the {len(items)} sellers Google Shopping lists",
                      "Established stores usually appear in Shopping results. Absence is not proof of a scam but adds doubt.",
                      [], pos, ["google_shopping"], absence=True)
    return unknown("seller", "market", "Known seller", "Not enough seller data",
                   "Google Shopping returned too few sellers to compare.", pos, ["google_shopping"])

def url_signal(url):
    pos, neg = _w("shop", "url")
    if not url:
        return unknown("url", "behaviour", "Website address", "No store link provided",
                       "Paste the link you were sent. Look-alike and throw-away domains are easy to spot.", neg, optional=True), None
    an = analyze_url(url)
    ev = [_ev("Domain", an["registrable"] or an["host"])] + [_ev(f["label"], f["why"]) for f in an["flags"][:4]]
    if an["penalty"] >= 14:
        return signal("url", "behaviour", "Website address", "fail", -an["penalty"],
                      f"{len(an['flags'])} warning signs in the web address", "The domain has several traits common to fake shops.",
                      ev, neg, [], critical=any(f["id"] == "impersonation" for f in an["flags"])), an
    if an["penalty"] > 0:
        return signal("url", "behaviour", "Website address", "warn", -an["penalty"],
                      f"{len(an['flags'])} minor warning sign{'s' if len(an['flags']) > 1 else ''} in the web address",
                      "None is conclusive alone, but together they look like a quickly-made shop.", ev, neg, []), an
    if an["clean"]:
        return signal("url", "behaviour", "Website address", "pass", pos, "Web address looks ordinary",
                      "Clean domain with a common ending. This is a weak positive on its own.", ev, neg, []), an
    return signal("url", "behaviour", "Website address", "info", 0, "No warning signs in the web address", "", ev, neg, []), an

def message_signal(mode, text):
    pos, neg = _w(mode, "message")
    if not text.strip():
        return unknown("message", "behaviour", "What they asked of you", "No message pasted",
                       "Paste the offer or chat text and TrustLens will highlight known scam phrases.", neg, optional=True), None
    an = analyze_message(text, mode)
    if not an["flags"]:
        return signal("message", "behaviour", "What they asked of you", "pass", pos,
                      "No known scam phrases in the message",
                      "The text does not ask for money, personal documents or urgency. That is a small positive.",
                      [], neg, [], optional=True), an
    ev = [_ev(f["label"], "\u201c" + f["matches"][0] + "\u201d") for f in an["flags"][:5]]
    status = "fail" if an["penalty"] >= 12 else "warn"
    return signal("message", "behaviour", "What they asked of you", status, -an["penalty"],
                  f"{len(an['flags'])} scam pattern{'s' if len(an['flags']) > 1 else ''} found in the message",
                  " ".join(f["why"] for f in an["flags"][:2]), ev, neg, [], critical=an["critical"]), an

def analyze_reviews(data):
    items, flagged = [], 0
    for r in (data.get("reviews") or [])[:10]:
        if not isinstance(r, dict):
            continue
        text = r.get("snippet") or (r.get("extracted_snippet") or {}).get("original") or ""
        low = text.lower()
        terms = [t for t in REVIEW_TERMS if t in low]
        flagged += bool(terms)
        user = r.get("user") or {}
        items.append({"rating": r.get("rating"), "text": text, "date": r.get("date"),
                      "user": user.get("name") if isinstance(user, dict) else None, "terms": terms})
    return {"items": items[:6], "flagged": flagged, "total": len(items)}

def reviews_signal(mode, an):
    pos, neg = _w(mode, "reviews")
    ev = [_ev(f"{i['rating']}\u2605 review", f"\u201c{i['text'][:110]}\u201d") for i in an["items"] if i["terms"]][:3]
    if an["total"] < 3:
        return unknown("reviews", "reputation", "What unhappy customers say", "Could not read enough reviews",
                       "Fewer than three of the lowest-rated reviews were available.", max(pos, neg), ["google_maps_reviews"])
    if an["flagged"] >= 3:
        return signal("reviews", "reputation", "What unhappy customers say", "fail", -neg,
                      f"{an['flagged']} of the lowest-rated reviews describe fraud, refunds or false promises",
                      "TrustLens read the lowest-rated reviews. The same complaints repeat, which points to a pattern rather than a one-off.",
                      ev, max(pos, neg), ["google_maps_reviews"])
    if an["flagged"] >= 1:
        return signal("reviews", "reputation", "What unhappy customers say", "warn", -6,
                      f"{an['flagged']} low-rated review mentions a serious complaint",
                      "One or two serious complaints exist. Read them for context.", ev, max(pos, neg), ["google_maps_reviews"])
    return signal("reviews", "reputation", "What unhappy customers say", "pass", pos,
                  "Even the lowest-rated reviews contain no fraud or refund complaints",
                  "The worst reviews are about ordinary matters such as waiting time, not about honesty.", [], max(pos, neg), ["google_maps_reviews"])
