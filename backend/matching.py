from __future__ import annotations
import difflib, re
from urllib.parse import urlparse

LEGAL = {"pvt", "private", "ltd", "limited", "llp", "inc", "incorporated", "corp", "corporation",
         "co", "company", "opc", "llc", "plc", "the", "and", "of"}
GENERIC = {"services", "service", "solutions", "solution", "technologies", "technology", "tech",
           "global", "group", "enterprises", "enterprise", "systems", "system", "consulting",
           "consultants", "outsourcing", "india", "international", "associates", "academy",
           "institute", "clinic", "center", "centre", "store", "stores", "shop", "outlet",
           "official", "online", "mart", "hub"}
SECOND_LEVEL = {"co.in", "org.in", "net.in", "gov.in", "ac.in", "edu.in", "res.in", "nic.in",
                "firm.in", "gen.in", "ind.in", "co.uk", "org.uk", "com.au", "co.nz", "co.za",
                "com.sg", "com.br"}
FREEMAIL = {"gmail.com", "yahoo.com", "yahoo.in", "yahoo.co.in", "outlook.com", "hotmail.com",
            "rediffmail.com", "proton.me", "protonmail.com", "icloud.com", "aol.com", "live.com",
            "ymail.com", "zohomail.in", "mail.com", "googlemail.com"}

def normalize(text: str) -> str:
    text = (text or "").lower().replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()

def tokens(text: str) -> list[str]:
    return normalize(text).split()

def core_tokens(name: str) -> list[str]:
    toks = [t for t in tokens(name) if t not in LEGAL]
    core = [t for t in toks if t not in GENERIC]
    return core or toks

def similarity(a: str, b: str) -> float:
    ca, cb = core_tokens(a), core_tokens(b)
    if not ca or not cb:
        return 0.0
    ja, jb = "".join(ca), "".join(cb)
    if ja == jb:
        return 1.0
    sa, sb = set(ca), set(cb)
    overlap = len(sa & sb)
    contain = overlap / min(len(sa), len(sb))
    ratio = difflib.SequenceMatcher(None, ja, jb).ratio()
    score = ratio
    if contain == 1.0:
        score = max(score, 0.85)
    elif overlap:
        score = max(score, 0.5 * overlap / len(sa | sb) + 0.25)
    return round(min(score, 1.0), 3)

def is_match(a: str, b: str, threshold: float = 0.75) -> bool:
    return similarity(a, b) >= threshold

def mentions(text: str, name: str) -> bool:
    core = core_tokens(name)
    if not core:
        return False
    t = normalize(text)
    if " ".join(core) in t:
        return True
    joined = "".join(core)
    if len(joined) >= 6 and joined in t.replace(" ", ""):
        return True
    words = set(t.split())
    if all(tok in words for tok in core) and (len(core) > 1 or len(core[0]) >= 4):
        return True
    return False

def host_of(url_or_host: str) -> str:
    raw = (url_or_host or "").strip()
    if not raw:
        return ""
    if "@" in raw and "://" not in raw:
        raw = raw.split("@", 1)[1]
    if "://" not in raw:
        raw = "http://" + raw
    host = (urlparse(raw).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host

def registrable(host: str) -> str:
    parts = [p for p in host.split(".") if p]
    if len(parts) <= 2:
        return host
    last2 = ".".join(parts[-2:])
    if last2 in SECOND_LEVEL and len(parts) >= 3:
        return ".".join(parts[-3:])
    return last2

def domain_label(host: str) -> str:
    return registrable(host).split(".")[0]

def domain_matches_company(host: str, company: str) -> bool:
    label = domain_label(host).replace("-", "")
    core = "".join(core_tokens(company))
    if not label or not core:
        return False
    if len(core) >= 4 and (core in label or (len(label) >= 5 and label in core)):
        return True
    return difflib.SequenceMatcher(None, label, core).ratio() >= 0.8

def pretty_from_host(host: str) -> str:
    return domain_label(host).replace("-", " ").replace("_", " ").title()
