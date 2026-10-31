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
    ("analyst", r"data analy|data engineer|business analy|business intelligence|analytics|\bmis\b|strategy|consult|"
                r"research analyst|growth analy|operations analy|market research"),
]
SWE = r"software (developer|engineer|development)|full.?stack|back.?end|front.?end|web developer|android|ios developer|sde|qa|test automation"
# Hand vetting after reading each ≥₹30k detail page (30 Oct 2026). Internshala lets anyone post,
# so a stated stipend is not proof the role is real; these are the calls made on the 32 cards found.
VETO = {
    "QuickHyre": "₹80,000–1,35,000/month for a 3-month work-from-home intern is far above the Indian market "
                 "(big-tech interns get ~₹1L); the poster is itself a job-board startup and has 4 such ads. Not trusted.",
    "Divonex Chemicals Private Limited": "field sales role",
    "Fin Maverick": "investment-banking/finance role, outside the role list; the poster is a test-prep community",
    "Eureka Forbes": "corporate sales role",
    "Finnup Global Services Private Limited": "corporate sales role",
    "KGM Gupta And Co. Chartered Accountants": "CA articleship",
}
# Kept, but the sheet carries a warning in the JD.
CAVEAT = {
    "Karanpreet Singh": "Posted by an individual, not a company: data-labelling work for frontier AI labs. Work from home.",
    "Sujith Kumar Gundala": "Posted by an individual whose page links only a LinkedIn profile, for independent MVP projects. Verify who you would work for before applying.",
    "Unnati Enterprises": "An apparel brand (Chikku Pikku) hiring 10 analytics interns at once; confirm the actual work.",
    "Axe Consultancy And Security Services LLC": "Small US-based IT-consulting firm; work from home.",
}
BAD = r"(content|social media|graphic|video|design(er|ing)?|marketing|sales|hr |human resource|recruit|telecall|teach|tutor|legal|account(s|ing)|ca intern|fundrais|photograph|copywrit)"


def clean(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or ""))).strip()


def parse_start(s, duration_text=""):
    """'Starts immediately' / '1 Nov' / '15 Dec'26' -> date, or None."""
    t = (s or "").strip().lower()
    if not t or "immediate" in t:
        return TODAY
    m = re.search(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*([a-z]{3})[a-z]*\s*'?\s*(\d{2,4})?", t)
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


def parse_deadline(s):
    d = parse_start(s or "")
    return f"{d:%Y-%m-%d}" if d and d != TODAY else ""


def months(duration_text):
    m = re.search(r"(\d+)\s*month", (duration_text or "").lower())
    return int(m.group(1)) if m else None


def track_of(title, about, skills):
    # The title decides; the blurb and skills only break ties. Check the wanted lists BEFORE the
    # veto list, or a blurb that merely mentions "marketing" sinks a genuine engineering role.
    for blob in (title.lower(), f"{title} {about} {skills}".lower()):
        for name, pat in WANTED:
            if re.search(pat, blob):
                return name
        if re.search(SWE, blob):
            return "swe"
        if re.search(BAD, blob):
            return None
    return None


def page_text(h):
    """Visible text with tags as '|' separators — the detail page has no stable class names."""
    t = re.sub(r"<script.*?</script>", "", h, flags=re.S)
    t = re.sub(r"<style.*?</style>", "", t, flags=re.S)
    t = html.unescape(re.sub(r"(\|\s*)+", "|", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "|", t))))
    return t.replace("\xa0", " ")


def section(t, start, *ends):
    i = t.find(start)
    if i < 0:
        return ""
    j = min([x for x in (t.find(e, i + len(start)) for e in ends) if x > 0] or [i + 2500])
    return t[i + len(start):j].strip(" |")


def detail(card):
    r = ats.get(card["url"], headers={"Accept": "text/html"})
    if r is None or r.status_code != 200:
        return {"closed": True, "why": f"HTTP {getattr(r, 'status_code', 'none')}"}
    t = page_text(r.text)
    if "404: Page not found" in t or "no longer accepting applications" in t.lower():
        return {"closed": True, "why": "page gone / not accepting"}
    who = section(t, "Who can apply", "Perks", "Number of openings", "About ")
    return {
        "closed": False,
        "start_raw": section(t, "Start Date", "Duration"),
        "start_window": (re.search(r"can start the internship between ([^|]+)", who) or [None, ""])[1].strip()
                        if "can start" in who else "",
        "duration": section(t, "Duration", "Stipend"),
        "stipend": section(t, "Stipend ", "APPLY BY", "Posted"),
        "apply_by": section(t, "APPLY BY", "Posted", "Job offer"),
        "applicants": (re.search(r"([\d,+]+) applicants", t) or [None, ""])[1],
        "post_offer": (re.search(r"Job offer starting \|?₹ ?([^|]+)", t) or [None, ""])[1].strip(),
        "openings": section(t, "Number of openings", "About "),
        "desc": section(t, "About the internship", "Skill(s) required", "Who can apply")[:1800],
        "skills": section(t, "Skill(s) required", "Earn certifications", "Who can apply")[:300],
        "who": who[:900],
        "part_time": "available for part time" in who.lower(),
        "in_office": "in-office" in who.lower(),
        "about_company": section(t, "About " + card["company"][:28], "Activity on Internshala", "Similar internships")[:700],
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
        if c["company"] in VETO:
            rejected.append({"company": c["company"], "role": c["title"], "url": c["url"],
                             "reason": VETO[c["company"]]})
            continue
        d = detail(c) or {}
        details[c["url"]] = d
        if d.get("closed"):
            rejected.append({"company": c["company"], "role": c["title"], "url": c["url"], "reason": "closed"})
            continue
        if re.search(r"phd|ph\.d|doctoral|master'?s (degree )?required|mba only", (c["title"] + " " + d.get("who", "") + " " + d.get("desc", "")), re.I):
            rejected.append({"company": c["company"], "role": c["title"], "url": c["url"],
                             "reason": "needs a PhD / Master's"})
            continue
        start = parse_start(re.split(r"\s+and\s+", d.get("start_window", ""))[0] or d.get("start_raw") or c.get("start"),
                            d.get("duration") or c["duration"])
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
            "duration": (d.get("duration") or c["duration"] or "not stated").strip(),
            "dates": (f"{start:%b %Y}" + (f" – {ends:%b %Y}" if ends else "")) if start else "not stated",
            "runs_past_may": bool(ends and ends > datetime.date(2027, 5, 31)),
            "exp": clean(d.get("who"))[:300] or "see posting",
            "_pt": d.get("part_time"), "_appl": d.get("applicants"), "_offer": d.get("post_offer"),
            "pay": c["stipend_text"].replace("₹ ", "₹"), "stipend_inr_month": c["stipend_inr_month"],
            "track": tr if tr != "swe" else "swe",
            "posted": "", "deadline": parse_deadline(d.get("apply_by")),
            "jd": (clean(d.get("desc"))[:430] or clean(c["about"])) + (f" Skills asked: {c['skills']}." if c["skills"] else ""),
            "li": c["company"], "resume": "DS / AI" if tr == "ai" else "SDE" if tr == "swe" else "Analyst / PM",
            "verified": "Internshala detail page 200 on 30 Oct 2026",
            "note": ("Apply via Internshala. " + CAVEAT.get(c["company"], "")).strip(),
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
