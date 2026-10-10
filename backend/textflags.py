from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any
from .matching import FREEMAIL, host_of, registrable, domain_label

RUPEE = r"(?:₹|rs\.?|inr)\s?"

@dataclass(frozen=True)
class Rule:
    id: str
    label: str
    points: int
    severity: str
    why: str
    patterns: tuple[str, ...]
    critical: bool = False

JOB_RULES = (
    Rule("fee_request", "Asks you to pay money", 25, "high",
         "Real employers never charge candidates for registration, training, kits or 'security'. "
         "This is the most common job-scam pattern in India.",
         (r"\b(registration|security|training|kit|processing|verification|joining|laptop|uniform|id[- ]?card|courier|onboarding)\s+(fee|fees|charges?|deposit|amount)\b",
          r"\brefundable\s+(deposit|amount|fee|fees)\b",
          rf"\b(pay|deposit|transfer|send)\b[^.\n]{{0,45}}{RUPEE}[\d,]+"), critical=True),
    Rule("task_scam", "Pays you for 'simple tasks'", 20, "high",
         "Like/subscribe/review 'tasks' that pay per action are a known scam that starts with small "
         "payouts and then asks you to deposit money.",
         (r"\b(like|subscribe|rate|review|follow)\b[^.\n]{0,30}\b(videos?|youtube|products?|hotels?|maps?|reels?|pages?)\b",
          r"\btasks?\b[^.\n]{0,25}\b(complete|earn|reward|commission)\b"), critical=True),
    Rule("sensitive_docs", "Wants Aadhaar / bank details early", 10, "medium",
         "Identity and bank details should only be shared after a verified offer letter, never over chat.",
         (r"\b(send|share|submit|provide|upload)\b[^.\n]{0,35}\b(aadhaar|aadhar|pan\b|bank (account )?details|cancelled cheque|otp|passport)\b",
          r"\b(aadhaar|aadhar|pan card|bank details|otp)\b[^.\n]{0,25}\b(required|needed|mandatory)\b")),
    Rule("earnings_claim", "Unrealistic daily earnings", 6, "medium",
         "Promises of thousands per day for simple work are not how genuine payroll works.",
         (rf"\b(earn|income|salary|make)\b[^.\n]{{0,30}}{RUPEE}[\d,]{{4,}}\s*(/|per|a|every)?\s*(day|daily|week|weekly)\b",
          r"\bearn\b[^.\n]{0,20}\bdaily\b")),
    Rule("no_interview", "'No interview' or instant selection", 6, "medium",
         "Legitimate hiring involves at least one interview or assessment.",
         (r"\bno interview\b", r"\bwithout (any )?(interview|test|assessment)\b",
          r"\bdirect(ly)?\s+(joining|selected|selection|offer)\b", r"\binstant(ly)?\s+(hiring|selection|joining)\b")),
    Rule("chat_only", "Moves you to WhatsApp / Telegram only", 6, "medium",
         "Scammers avoid official channels. A real recruiter can email from a company domain and share a careers link.",
         (r"\b(contact|apply|message|reach|confirm|reply|join)\b[^.\n]{0,40}\b(whatsapp|telegram)\b",
          r"\b(whatsapp|telegram)\s+(only|group|channel)\b")),
    Rule("no_experience_pay", "High pay with no qualification", 6, "medium",
         "Pay this high with 'no experience' is a bait pattern.",
         (rf"\bno\s+(experience|qualification|degree|skills?)\b[^.\n]{{0,45}}{RUPEE}[\d,]{{5,}}",)),
    Rule("urgency", "Pressure to act quickly", 2, "low",
         "Urgency stops you from checking. Genuine offers can wait a day.",
         (r"\b(limited|only\s+\d+)\s+(seats?|slots?|vacanc(?:y|ies)|positions?)\b", r"\bhurry\b",
          r"\blast date\s+(is\s+)?(today|tomorrow)\b", r"\bapply\s+(immediately|now|today)\b")),
)

SHOP_RULES = (
    Rule("personal_upi", "Payment to a personal UPI / QR", 18, "high",
         "Paying an individual UPI ID or QR removes all buyer protection. Legitimate stores use a payment gateway.",
         (r"\b(upi|gpay|google pay|phonepe|paytm)\b[^.\n]{0,35}\b(only|number|id)\b",
          r"\bscan\s+(the\s+)?qr\b", r"\bpay(ment)?\s+to\s+(my|our|this|personal)\b",
          r"\bsend\s+(the\s+)?screenshot\b"), critical=True),
    Rule("advance_only", "Full advance payment, no COD", 16, "high",
         "Demanding all the money first with no cash-on-delivery is how fake stores avoid accountability.",
         (r"\b(100\s?%|full|entire|complete)\s+(advance\s+)?(payment|amount)\b", r"\badvance\s+(payment|amount)\b",
          r"\bpay(ment)?\s+(first|in advance|upfront|up front)\b", r"\bno\s+(cod|cash on delivery)\b")),
    Rule("extra_fees", "Extra fees before delivery", 16, "high",
         "Surprise 'customs', 'clearance' or 'insurance' fees after you pay are a classic add-on scam.",
         (r"\b(customs|duty|clearance|insurance|delivery|gst)\s+(fee|charge|payment)s?\b[^.\n]{0,30}\b(before|first|advance)\b",)),
    Rule("no_returns", "No returns or refunds", 6, "medium",
         "Established sellers publish a return policy.",
         (r"\bno\s+(returns?|refunds?|exchange|replacement)\b", r"\bfinal sale\b", r"\bnon[- ]refundable\b")),
    Rule("chat_order", "Order only by DM / WhatsApp", 6, "medium",
         "Taking orders through chat keeps the seller untraceable.",
         (r"\b(dm|whatsapp|message|inbox)\s+(to|for)\s+(order|buy|book|price)\b",
          r"\border\s+(on|via|through)\s+(whatsapp|dm|instagram)\b")),
    Rule("mega_discount", "Extreme discount", 6, "medium",
         "Discounts of 80-90% on branded goods are a bait signal.",
         (r"\b(7\d|8\d|9\d)\s?%\s*(off|discount)\b",)),
    Rule("pressure", "Countdown / scarcity pressure", 3, "low",
         "'Only 3 left' and 'today only' push you to pay before you think.",
         (r"\b(only|just)\s+\d+\s+(pieces|pcs|left|units|in stock)\b", r"\boffer\s+(ends|expires)\b",
          r"\btoday only\b", r"\blimited stock\b", r"\bflash sale\b", r"\bhurry\b")),
)

LOCAL_RULES = (
    Rule("guaranteed", "Guaranteed results", 14, "high",
         "'Guaranteed selection / placement / cure' cannot be honestly promised by any genuine service.",
         (r"\b(100\s?%|guaranteed)\s+(placement|selection|result|results|job|admission|success|cure|returns?|visa)\b",
          r"\bguarantee[sd]?\s+(you\s+)?(a\s+)?(job|selection|rank|admission)\b"), critical=True),
    Rule("advance_only", "Full payment upfront", 14, "high",
         "Asking for the entire fee before any service is delivered removes your leverage if things go wrong.",
         (r"\b(100\s?%|full|entire|complete)\s+(advance\s+)?(payment|fee|fees)\b", r"\badvance\s+(payment|fee|fees|amount)\b",
          r"\bpay(ment)?\s+(first|in advance|upfront|up front)\b", r"\bupfront\b")),
    Rule("no_refund", "Refuses refunds", 8, "medium",
         "A clear refund policy is normal for genuine institutions.",
         (r"\bno\s+refunds?\b", r"\bnon[- ]refundable\b", r"\brefund\b[^.\n]{0,20}\b(not possible|not allowed|under any)\b")),
    Rule("cash_only", "Cash only, no bill", 6, "medium",
         "No invoice or receipt means no proof of payment.",
         (r"\bcash only\b", r"\bonly cash\b", r"\bno\s+(invoice|bill|receipt)\b")),
    Rule("pressure", "Pressure to decide today", 3, "low",
         "Pressure tactics are used to stop you comparing options.",
         (r"\b(only|just)\s+\d+\s+(seats?|slots?|left)\b", r"\boffer\s+(ends|expires)\b", r"\btoday only\b", r"\bhurry\b")),
)

RULES = {"job": JOB_RULES, "shop": SHOP_RULES, "local": LOCAL_RULES}
MESSAGE_CAP = 35

def _dedupe(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for m in sorted(matches, key=lambda x: -(x["end"] - x["start"])):
        if not any(k["start"] <= m["start"] and m["end"] <= k["end"] for k in kept):
            kept.append(m)
    return sorted(kept, key=lambda x: x["start"])

def analyze_message(text: str, mode: str) -> dict[str, Any]:
    text = text or ""
    flags: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []
    total = 0
    for rule in RULES.get(mode, ()):
        matches: list[dict[str, Any]] = []
        for pat in rule.patterns:
            for m in re.finditer(pat, text, flags=re.I):
                matches.append({"start": m.start(), "end": m.end(), "text": m.group(0)})
        matches = _dedupe(matches)
        if not matches:
            continue
        total += rule.points
        flags.append({"id": rule.id, "label": rule.label, "severity": rule.severity, "why": rule.why,
                      "points": rule.points, "critical": rule.critical, "matches": [x["text"] for x in matches[:3]]})
        for m in matches:
            spans.append({**m, "rule": rule.id, "label": rule.label, "severity": rule.severity})
    return {"flags": flags, "highlights": _merge_spans(spans), "penalty": min(total, MESSAGE_CAP),
            "critical": any(f["critical"] for f in flags), "text": text}

def _merge_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {"high": 0, "medium": 1, "low": 2}
    spans = sorted(spans, key=lambda s: (s["start"], order[s["severity"]], -(s["end"] - s["start"])))
    out: list[dict[str, Any]] = []
    for s in spans:
        if out and s["start"] < out[-1]["end"]:
            if order[s["severity"]] < order[out[-1]["severity"]] and s["start"] == out[-1]["start"]:
                out[-1] = s
            continue
        out.append(s)
    return out

RISKY_TLDS = {"top", "xyz", "click", "shop", "online", "site", "icu", "buzz", "vip", "work", "rest",
              "cfd", "sbs", "bond", "cyou", "monster", "fun", "live", "store", "life", "today", "cam"}
SHORTENERS = {"bit.ly", "tinyurl.com", "rb.gy", "cutt.ly", "is.gd", "t.co", "wa.me", "goo.gl", "shorturl.at"}
COMMON_TLDS = {"com", "in", "org", "net", "edu", "gov", "io", "co"}
PROMO_WORDS = ("official", "outlet", "clearance", "sale", "offer", "deals", "dealz", "discount", "cheap", "wholesale")

BRANDS = {
    "amazon": {"amazon.in", "amazon.com", "amazonaws.com", "amazon.jobs"}, "flipkart": {"flipkart.com"},
    "myntra": {"myntra.com"}, "apple": {"apple.com"}, "iphone": {"apple.com"}, "samsung": {"samsung.com"},
    "sony": {"sony.co.in", "sony.com"}, "nike": {"nike.com"}, "adidas": {"adidas.co.in", "adidas.com"},
    "paytm": {"paytm.com"}, "phonepe": {"phonepe.com"}, "sbi": {"sbi.co.in", "onlinesbi.sbi"},
    "hdfc": {"hdfcbank.com"}, "icici": {"icicibank.com"}, "airtel": {"airtel.in"}, "jio": {"jio.com"},
    "meesho": {"meesho.com"}, "nykaa": {"nykaa.com"}, "ajio": {"ajio.com"}, "swiggy": {"swiggy.com"},
    "zomato": {"zomato.com"}, "irctc": {"irctc.co.in"}, "infosys": {"infosys.com"}, "wipro": {"wipro.com"},
    "tcs": {"tcs.com"}, "accenture": {"accenture.com"}, "google": {"google.com"}, "microsoft": {"microsoft.com"},
    "deloitte": {"deloitte.com"}, "cognizant": {"cognizant.com"}, "capgemini": {"capgemini.com"},
}

def analyze_url(url: str) -> dict[str, Any]:
    raw = (url or "").strip()
    host = host_of(raw)
    if not host:
        return {"host": "", "registrable": "", "flags": [], "penalty": 0, "clean": False}
    reg = registrable(host)
    label = domain_label(host)
    tld = reg.split(".")[-1]
    flags: list[dict[str, Any]] = []

    def add(id_, label_, points, why):
        flags.append({"id": id_, "label": label_, "points": points, "why": why})

    if raw.lower().startswith("http://"):
        add("no_https", "Not using HTTPS", 4, "Checkout pages without HTTPS can expose your card and UPI details.")
    if reg in SHORTENERS or host in SHORTENERS:
        add("shortener", "Link shortener hides the real site", 8, "Shorteners are used to disguise where a link really goes.")
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
        add("ip_host", "Site is a raw IP address", 10, "Real businesses use a proper domain name.")
    if "xn--" in host:
        add("punycode", "Look-alike characters in domain", 8, "Punycode domains can imitate a well-known brand with foreign letters.")
    if tld in RISKY_TLDS:
        add("risky_tld", f"Cheap '.{tld}' domain ending", 4, "Not proof of fraud, but very common on throw-away shops.")
    if label.count("-") >= 2:
        add("hyphens", "Several hyphens in the domain", 4, "Long hyphenated names are typical of quickly-made scam sites.")
    if sum(c.isdigit() for c in label) >= 3:
        add("digits", "Many digits in the domain", 3, "Random numbers in a domain suggest an auto-generated site.")
    if any(w in label for w in PROMO_WORDS):
        add("promo_words", "'Official / outlet / clearance' in the name", 5, "Scam shops add these words to look authentic. Real brands rarely need to.")
    if len(label) > 24:
        add("long_label", "Unusually long domain", 2, "Very long domains are hard to verify by eye.")
    if len(host.split(".")) - len(reg.split(".")) >= 3:
        add("subdomains", "Deeply nested sub-domains", 4, "Extra sub-domains can hide the real site name.")
    for brand, official in BRANDS.items():
        if brand in label and reg not in official:
            add("impersonation", f"Uses the '{brand}' name but is not their site", 14,
                f"The domain contains '{brand}' but is not one of that brand's official domains.")
            break

    penalty = min(sum(f["points"] for f in flags), 24)
    clean = (not flags) and tld in COMMON_TLDS
    return {"host": host, "registrable": reg, "flags": flags, "penalty": penalty, "clean": clean}

def is_freemail(host: str) -> bool:
    return registrable(host) in FREEMAIL or host in FREEMAIL
