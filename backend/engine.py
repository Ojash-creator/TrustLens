from __future__ import annotations
import hashlib, re
from typing import Any, Callable
from . import signals as S
from .matching import host_of, pretty_from_host, registrable
from .serp import utc_now_iso

MODE_LABEL = {"job": "Job offer", "shop": "Online shop", "local": "Local business"}
VERDICTS = {"high_risk": "High risk", "caution": "Proceed with caution",
            "trustworthy": "Looks legitimate", "insufficient": "Not enough evidence"}
HEADLINES = {
    "high_risk": {"job": "Do not pay any fee or share documents.", "shop": "Do not pay this store.",
                  "local": "Do not pay in advance."},
    "caution": {"job": "Verify the employer before you go further.", "shop": "Verify the seller before you pay.",
                "local": "Verify the business before you commit."},
    "trustworthy": {"job": "No serious warning signs found for this offer.", "shop": "No serious warning signs found for this store.",
                    "local": "No serious warning signs found for this business."},
    "insufficient": {"job": "Public data is too thin to judge this offer.", "shop": "Public data is too thin to judge this store.",
                     "local": "Public data is too thin to judge this business."},
}

def clean_inputs(mode, raw):
    def s(key, limit=300):
        return re.sub(r"\s+", " ", str(raw.get(key) or "")).strip()[:limit]
    inp = {"name": s("name"), "role": s("role"), "location": s("location"), "email": s("email"),
           "url": s("url", 500), "product": s("product"), "price": s("price", 30),
           "message": str(raw.get("message") or "").strip()[:4000]}
    if mode == "job" and len(inp["name"]) < 2:
        raise ValueError("Enter the company name from the job offer.")
    if mode == "local" and len(inp["name"]) < 2:
        raise ValueError("Enter the business name.")
    if mode == "shop":
        if not (inp["name"] or inp["url"] or inp["product"]):
            raise ValueError("Enter a store name, a store link or a product.")
        if not inp["name"] and inp["url"]:
            inp["name"] = pretty_from_host(host_of(inp["url"]))
    return inp

def _coverage(client, mode, name, domain=""):
    ident = f'"{name}"' + (f' OR "{domain}"' if domain else "")
    web = client.search("google", "web", q=f"{ident} scam OR fraud OR fake OR complaints OR reviews", num=10)
    results = list(web.get("organic_results") or [])
    an = S.analyze_web(name, results, domain)
    followup = False
    if an["strong"] >= 1:
        fu = client.search("google", "followup", q=f'{name} reddit OR quora OR "consumer complaint" experience', num=10)
        seen = {r.get("link") for r in results}
        results += [r for r in (fu.get("organic_results") or []) if r.get("link") not in seen]
        an = S.analyze_web(name, results, domain)
        followup = True
    web_sig = S.web_signal(name, an, followup)
    news = client.search("google_news", "news", q=f'"{name}"')
    nan = S.analyze_news(name, news)
    news_sig = S.news_signal(mode, name, nan)
    return {"signals": [web_sig, news_sig], "web": an["items"], "news": nan["items"]}, an, nan

def _reviews_step(client, mode, place):
    if not place.get("data_id"):
        return None, []
    data = client.search("google_maps_reviews", "reviews", data_id=place["data_id"], sort_by="ratingLow",
                         label=f"lowest-rated reviews of {place['title']}")
    an = S.analyze_reviews(data)
    return S.reviews_signal(mode, an), an["items"]

def _job(inp, client):
    name, role, loc = inp["name"], inp["role"], inp["location"]
    sigs, panels = [], {}
    maps = client.search("google_maps", "maps", q=f"{name} {loc}".strip())
    place, near = S.pick_place(maps, name)
    panels.update(place=place, near=near)
    sigs.append(S.maps_presence_signal("job", name, place, near))
    if place:
        sigs.append(S.maps_reputation_signal("job", place))
    if role:
        jobs = client.search("google_jobs", "jobs", q=" ".join(x for x in (role, name, loc) if x))
        sig, views = S.job_posting_signal(name, role, jobs)
        sigs.append(sig); panels["jobs"] = views
    else:
        sigs.append(S.unknown("job_posting", "market", "Listed on Google Jobs", "No role provided",
                              "Add the job title to check whether the company advertises it publicly.", 16, ["google_jobs"], optional=True))
    if place and (place.get("rating") or 5) < 3.6 and place.get("reviews", 0) >= 5:
        sig, reviews = _reviews_step(client, "job", place)
        if sig:
            sigs.append(sig); panels["reviews"] = reviews
    website = place.get("website") if place else None
    sigs.append(S.recruiter_signal(name, inp["email"], website))
    msig, man = S.message_signal("job", inp["message"])
    sigs.append(msig); panels["message"] = man
    cov, _, _ = _coverage(client, "job", name, registrable(host_of(website)) if website else "")
    sigs += cov["signals"]; panels.update(web=cov["web"], news=cov["news"])
    return sigs, panels

def _shop(inp, client):
    name, url, product = inp["name"], inp["url"], inp["product"]
    listed = S._num(inp["price"])
    host = host_of(url)
    sigs, panels = [], {}
    if product:
        shop = client.search("google_shopping", "shopping", q=product)
        psig, pan = S.price_signal(listed, shop)
        sigs += [psig, S.seller_signal(inp["name"], shop)]
        panels["prices"] = pan
    else:
        sigs.append(S.unknown("price", "market", "Price against the market", "No product provided",
                              "Enter the product name and the price you were shown to compare it with the market.", 26,
                              ["google_shopping"], optional=True))
    if name:
        maps = client.search("google_maps", "maps", q=name)
        place, near = S.pick_place(maps, name)
        panels.update(place=place, near=near)
        sigs.append(S.maps_presence_signal("shop", name, place, near))
        if place:
            sigs.append(S.maps_reputation_signal("shop", place))
    usig, uan = S.url_signal(url)
    sigs.append(usig); panels["url"] = uan
    msig, man = S.message_signal("shop", inp["message"])
    sigs.append(msig); panels["message"] = man
    if name or host:
        cov, _, _ = _coverage(client, "shop", name or host, registrable(host) if host else "")
        sigs += cov["signals"]; panels.update(web=cov["web"], news=cov["news"])
    return sigs, panels

def _local(inp, client):
    name, loc = inp["name"], inp["location"]
    sigs, panels = [], {}
    maps = client.search("google_maps", "maps", q=f"{name} {loc}".strip())
    place, near = S.pick_place(maps, name)
    panels.update(place=place, near=near)
    sigs.append(S.maps_presence_signal("local", name, place, near))
    if place:
        sigs.append(S.maps_reputation_signal("local", place))
        sigs.append(S.contact_signal("local", place))
        sig, reviews = _reviews_step(client, "local", place)
        if sig:
            sigs.append(sig); panels["reviews"] = reviews
    msig, man = S.message_signal("local", inp["message"])
    sigs.append(msig); panels["message"] = man
    website = place.get("website") if place else None
    cov, _, _ = _coverage(client, "local", name, registrable(host_of(website)) if website else "")
    sigs += cov["signals"]; panels.update(web=cov["web"], news=cov["news"])
    return sigs, panels

PLANNERS: dict[str, Callable] = {"job": _job, "shop": _shop, "local": _local}

def score_signals(sigs):
    raw = 50 + sum(s["points"] for s in sigs)
    score = max(3, min(97, raw))
    known = sum(s["weight"] for s in sigs if s["status"] != "unknown")
    total = sum(s["weight"] for s in sigs if not (s["status"] == "unknown" and s["optional"]))
    confidence = round(100 * known / total) if total else 0
    return score, min(confidence, 100)

def decide(score, confidence, sigs):
    critical = any(s["critical"] and s["status"] in ("fail", "warn") for s in sigs)
    if critical:
        return "high_risk" if score < 60 else "caution"
    if confidence < 40:
        return "insufficient"
    if score < 45:
        has_hard_evidence = any(s["status"] in ("fail", "warn") and not s.get("absence") for s in sigs)
        return "high_risk" if has_hard_evidence else "insufficient"
    if score >= 72:
        return "trustworthy"
    return "caution"

def next_steps(mode, level, sigs):
    ids = {s["id"] for s in sigs if s["status"] in ("fail", "warn")}
    steps = []
    def add(title, body):
        steps.append({"title": title, "body": body})
    if level == "high_risk":
        if mode == "job":
            add("Do not pay anything", "Genuine employers never charge registration, training or 'security' fees. If money has already left your account, call 1930 or report at cybercrime.gov.in as soon as possible.")
            add("Do not share Aadhaar, PAN or bank details", "Keep identity documents until you hold a verified offer letter from a company you have confirmed independently.")
        elif mode == "shop":
            add("Do not pay this store", "If you already paid by UPI or card, contact your bank immediately and report at cybercrime.gov.in or on 1930.")
            add("Buy from a marketplace with buyer protection", "Use a seller Google Shopping already lists, and prefer cash on delivery or card payment.")
        else:
            add("Do not pay in advance", "Pay only against a written fee structure, a refund policy and a proper receipt.")
            add("Visit in person first", "Meet staff at the address on the listing and ask for references from current customers.")
        add("Report and warn others", "Report to the National Consumer Helpline (1915) or cybercrime.gov.in, and warn the group that forwarded this to you.")
    elif level == "caution":
        add("Verify through an independent channel", "Find the official contact details yourself from the company website or Google Maps listing and call to confirm the offer.")
        if mode == "job":
            add("Ask for a written offer on company letterhead", "Confirm the recruiter's name on LinkedIn and ask for an e-mail from the company domain.")
        if mode == "shop":
            add("Pay with protection", "Prefer cash on delivery or a card. Avoid paying to a personal UPI ID.")
        if mode == "local":
            add("Get the terms in writing", "Ask for the fee structure, refund terms and a receipt before paying.")
    elif level == "trustworthy":
        add("Still confirm the basics", "Check that the phone number and e-mail you were given match the ones on the official listing.")
        add("Keep records", "Save the offer letter, invoice or receipt in case anything changes later.")
    else:
        add("Collect more information", "Ask for the official website, a registered address and a contact number, then run the check again.")
        add("Do not pay yet", "With so little public data, treat any payment request as unverified.")
    if "recruiter" in ids:
        add("Ask for an official e-mail", "Request that the recruiter writes from an address on the company's own domain.")
    if "price" in ids:
        add("Compare with a known seller", "Open the top Google Shopping seller for the same product and check the price and warranty.")
    return steps[:5]

def _plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"

def build_summary(level, mode, sigs, searches):
    fails = [s for s in sigs if s["status"] == "fail"]
    warns = [s for s in sigs if s["status"] == "warn"]
    passes = [s for s in sigs if s["status"] == "pass"]
    ranked = sorted((s for s in sigs if s["status"] != "unknown" and s["points"] != 0), key=lambda s: -abs(s["points"]))
    top = [s for s in ranked if s["points"] < 0][:3] if level in ("high_risk", "caution") else ([s for s in ranked if s["points"] > 0][:3] or ranked[:3])
    reasons = [{"signal_id": s["id"], "title": s["title"], "text": s["finding"], "points": s["points"]} for s in top]
    body = (f"TrustLens ran {_plural(searches, 'search')} and found {_plural(len(fails), 'red flag')}, "
            f"{_plural(len(warns), 'caution')} and {_plural(len(passes), 'reassuring signal')}.")
    if reasons:
        body += f" The biggest factor: {reasons[0]['text'][0].lower() + reasons[0]['text'][1:]}."
    return body, reasons

def run_check(mode, raw, client, *, source="live", sample_id=None, explainer=None):
    if mode not in PLANNERS:
        raise ValueError("Unknown check type.")
    inp = clean_inputs(mode, raw)
    sigs, panels = PLANNERS[mode](inp, client)
    score, confidence = score_signals(sigs)
    level = decide(score, confidence, sigs)
    usage = client.usage()
    summary, reasons = build_summary(level, mode, sigs, max(usage["searches"], len(client.trace)))
    ident = f"{mode}|{inp['name']}|{inp['url']}|{utc_now_iso()}"
    report = {
        "id": "TL-" + hashlib.sha1(ident.encode()).hexdigest()[:8].upper(),
        "generated_at": utc_now_iso(), "mode": mode, "mode_label": MODE_LABEL[mode],
        "source": source, "sample_id": sample_id, "inputs": inp, "entity": inp["name"] or host_of(inp["url"]),
        "score": score,
        "verdict": {"level": level, "label": VERDICTS[level], "headline": HEADLINES[level][mode]},
        "confidence": {"pct": confidence, "level": "high" if confidence >= 70 else "medium" if confidence >= 45 else "low"},
        "summary": summary, "summary_source": "rules", "reasons": reasons,
        "counts": {"fail": sum(s["status"] == "fail" for s in sigs), "warn": sum(s["status"] == "warn" for s in sigs),
                   "pass": sum(s["status"] == "pass" for s in sigs), "unknown": sum(s["status"] == "unknown" for s in sigs)},
        "signals": sigs,
        "waterfall": sorted(({"id": s["id"], "title": s["title"], "points": s["points"]} for s in sigs if s["points"]),
                            key=lambda x: -abs(x["points"])),
        "panels": panels, "next_steps": next_steps(mode, level, sigs),
        "trace": client.trace, "usage": usage, "notes": [],
    }
    if source == "demo" and not any(t["status"] == "ok" for t in client.trace):
        report["notes"].append("Demo mode only has recorded data for the sample cases. Add a SerpApi key to check anything you like.")
    if explainer:
        try:
            text = explainer(report)
            if text:
                report["summary"], report["summary_source"] = text, "claude"
        except Exception:
            pass
    return report
