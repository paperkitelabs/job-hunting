"""Turns crawl-internshala.json into screen-startups.json for the Startups sheet.

Fetches each ≥₹30k card's detail page for start date, duration, eligibility and the full
description, then screens on the candidate's rules:
  - start date between now and END_START (the internship must run inside Nov 2026 – May 2027)
  - role in the wanted list (PM/product, data/business analyst, strategy, data science, AI/ML, FDE)
  - India or work-from-home
Every row keeps the Internshala link and is flagged "apply via Internshala"; where the same
opening exists on the company's own careers site, put that URL in `url` instead by hand.

Run from the repo root:  python3 data/raw/internships/internshala_screen.py
"""
import datetime, html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ats  # noqa: E402

TODAY = datetime.date(2026, 10, 30)
END_START = datetime.date(2027, 2, 28)   # must start by then to do real work before May 2027
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

WANTED = [
    ("ai", r"data scien|machine learning|\bml\b|\bai\b|artificial intelligence|deep learning|nlp|generative|llm|"
           r"applied scien|computer vision|forward deployed|quant"),
    ("pm", r"product manage|product analyst|\bapm\b|associate product|product intern|product owner"),
    ("analyst", r"data analy|business analy|business intelligence|analytics|\bmis\b|strategy|consult|"
                r"research analyst|growth analy|operations analy|market research"),
]
SWE = r"software (developer|engineer|development)|full.?stack|back.?end|front.?end|web developer|android|ios developer|sde|qa|test automation"
BAD = r"(content|social media|graphic|video|design(er|ing)?|marketing|sales|hr |human resource|recruit|telecall|teach|tutor|legal|account(s|ing)|ca intern|fundrais|photograph|copywrit)"


def clean(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or ""))).strip()


def parse_start(s, duration_text=""):
    """'Starts immediately' / '1 Nov' / '15 Dec'26' -> date, or None."""
    t = (s or "").strip().lower()
    if not t or "immediate" in t:
        return TODAY
    m = re.search(r"(\d{1,2})\s*([a-z]{3})\s*'?(\d{2,4})?", t)
    if not m:
        return None
    day, mon, yr = int(m.group(1)), MONTHS.get(m.group(2)), m.group(3)
    if not mon:
        return None
    year = int(yr) + 2000 if yr and len(yr) == 2 else int(yr) if yr else (TODAY.year if mon >= TODAY.month else TODAY.year + 1)
    try:
        return datetime.date(year, mon, day)
    except ValueError:
        return None


def months(duration_text):
    m = re.search(r"(\d+)\s*month", (duration_text or "").lower())
    return int(m.group(1)) if m else None


def track_of(title, about, skills):
    blob = f"{title} {about} {skills}".lower()
    if re.search(BAD, blob) and not re.search(r"data|analy|machine learning|product manage", blob):
        return None
    for name, pat in WANTED:
        if re.search(pat, blob):
            return name
    if re.search(SWE, blob):
        return "swe"
    return None


def detail(card):
    r = ats.get(card["url"], headers={"Accept": "text/html"})
    if r is None or r.status_code != 200:
        return None
    h = r.text
    if "no longer available" in h.lower() or "internship is closed" in h.lower():
        return {"closed": True}

    def grab(pat):
        m = re.search(pat, h, re.S)
        return clean(m.group(1)) if m else ""

    return {
        "closed": False,
        "start": grab(r'Start Date</div>.*?<div[^>]*>(.*?)</div>') or grab(r'id="start-date-first">(.*?)</span>'),
        "duration": grab(r'Duration</div>.*?<div[^>]*>(.*?)</div>'),
        "apply_by": grab(r'Apply By</div>.*?<div[^>]*>(.*?)</div>'),
        "openings": grab(r'Openings?</div>.*?<div[^>]*>(.*?)</div>'),
        "stipend": grab(r'Stipend</div>.*?<span[^>]*>(.*?)</span>'),
        "about_company": grab(r'About (?:the company|[^<]*)</div>\s*<div[^>]*>(.*?)</div>')[:600],
        "desc": grab(r'About the (?:internship|work from home internship)</div>\s*<div[^>]*>(.*?)</div>')[:2500],
        "who": grab(r"Who can apply</div>\s*<div[^>]*>(.*?)</div>")[:1200],
        "perks": grab(r'Perks</div>\s*<div[^>]*>(.*?)</div>')[:300],
    }


def city_rank(loc):
    l = (loc or "").lower()
    for n, pat in [(1, r"mumbai|thane|navi"), (2, r"pune"), (3, r"bangalore|bengaluru")]:
        if re.search(pat, l):
            return n
    return 5 if "work from home" in l or "remote" in l else 4


def main():
    src = json.load(open(os.path.join(HERE, "crawl-internshala.json"), encoding="utf-8"))
    openings, rejected, swe, details = [], [], [], {}
    for c in src["cards"]:
        tr = track_of(c["title"], c["about"], c["skills"])
        if tr is None:
            rejected.append({"company": c["company"], "role": c["title"], "url": c["url"],
                             "reason": "outside the role list"})
            continue
        d = detail(c) or {}
        details[c["url"]] = d
        if d.get("closed"):
            rejected.append({"company": c["company"], "role": c["title"], "url": c["url"], "reason": "closed"})
            continue
        start = parse_start(d.get("start") or c.get("start"), d.get("duration") or c["duration"])
        if start and start > END_START:
            rejected.append({"company": c["company"], "role": c["title"], "url": c["url"],
                             "reason": f"starts {start:%b %Y}, too late for the Nov 2026 – May 2027 window"})
            continue
        dur = months(d.get("duration") or c["duration"])
        ends = None
        if start and dur:
            m = start.month - 1 + dur
            ends = datetime.date(start.year + m // 12, m % 12 + 1, 1)
        row = {
            "company": c["company"], "role": c["title"], "url": c["url"],
            "location": c["location"], "city_rank": city_rank(c["location"]),
            "job_id": "Internshala " + c["id"],
            "duration": d.get("duration") or c["duration"] or "not stated",
            "dates": (f"{start:%b %Y}" + (f" – {ends:%b %Y}" if ends else "")) if start else "not stated",
            "runs_past_may": bool(ends and ends > datetime.date(2027, 5, 31)),
            "exp": clean(d.get("who"))[:300] or "see posting",
            "pay": c["stipend_text"].replace("₹ ", "₹"), "stipend_inr_month": c["stipend_inr_month"],
            "track": tr if tr != "swe" else "swe",
            "posted": "", "deadline": "",
            "jd": (clean(d.get("desc"))[:420] or clean(c["about"])) + (f" Skills asked: {c['skills']}." if c["skills"] else ""),
            "li": c["company"], "resume": "DS / AI" if tr == "ai" else "SDE" if tr == "swe" else "Analyst / PM",
            "verified": "Internshala detail page 200 on 30 Oct 2026",
            "note": "Apply via Internshala (the company does not list this on its own careers site).",
        }
        (swe if tr == "swe" else openings).append(row)

    base = {"checked": "30 Oct 2026", "round1": [],
            "companies": [{"name": c, "ats": "internshala", "endpoint": "internshala.com",
                           "india_intern_hits": 1, "kept": 1, "note": "found via the Internshala stipend sweep"}
                          for c in sorted({o["company"] for o in openings + swe})]}
    ats.save(os.path.join(HERE, "screen-startups-internshala.json"),
             dict(base, cluster="internshala-stipend-30k", openings=openings, rejected=rejected))
    ats.save(os.path.join(HERE, "screen-swe-internshala.json"),
             dict(base, cluster="internshala-stipend-30k-swe", openings=swe, rejected=[]))
    ats.save(os.path.join(HERE, "crawl-internshala-details.json"), details)
    print(f"{len(src['cards'])} cards ≥₹30k -> {len(openings)} kept, {len(swe)} software-engineering, {len(rejected)} rejected")
    for o in sorted(openings, key=lambda x: (x["city_rank"], -(x["stipend_inr_month"] or 0))):
        print(f"  {o['pay']:28} {o['company'][:26]:26} {o['role'][:38]:38} {o['location'][:16]:16} {o['dates']}")


if __name__ == "__main__":
    main()
