"""Builds data/applications-internships.js from the round-3 screen_*.json files in this folder.
Run from the repo root:  python3 data/raw/internships/build_internships.py
Reads screen_*.json (openings + rejected), dedups, assigns tiers, sorts by city preference, writes the tracker file."""
import json, glob, re, os, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHECKED = datetime.date(2026, 10, 31)
SOON_DAYS = 10
TIERS = {
    "soon": "Closing soon: apply this week",
    "bfsi": "Banks, financial services and insurance",
    "consult": "Consulting, Big 4 and analytics firms",
    "pm": "Product: APM, product analyst and PM interns",
    "analyst": "Data and business analyst interns, other companies",
    "ai": "Data science, AI/ML and forward deployed interns",
    "swe": "Software engineering interns",
    "nostip": "Stipend not stated: ask before you apply (your floor is ₹30,000/month)",
}
ORDER = list(TIERS)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60]


def parse_date(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return datetime.date(*map(int, m.groups())) if m else None


def short_date(d):
    return f"{d.day} {MONTHS[d.month - 1]}"


def type_line(o):
    parts = ["Internship"]
    dur = (o.get("duration") or "").strip()
    dates = (o.get("dates") or "").strip()
    dur_s = re.sub(r"\s*months?\b", " mo", dur, flags=re.I) if dur and dur.lower() != "not stated" else ""
    dates_s = dates if dates and dates.lower() != "not stated" else ""
    if dur_s and dates_s:
        parts.append(f"{dur_s}, {dates_s}")
    elif dur_s or dates_s:
        parts.append(dur_s or dates_s)
    else:
        parts.append("dates not stated")
    if o.get("runs_past_may"):
        parts.append("runs past May")
    return " · ".join(parts)


SHEETS = {  # key -> (screen-file glob, tab label, order)
    "main": ("screen_*.json", "MNCs & top companies", 1),
    "startups": ("screen-startups*.json", "Startups (₹30k+ stipend)", 2),
    "swe": ("screen-swe*.json", "Plain roles (software engineering)", 3),
}
MIN_STIPEND = 30000


def stipend(o):
    """Monthly stipend in rupees from stipend_inr_month or the pay text ('₹40,000/month', '40k'); None if unstated."""
    v = o.get("stipend_inr_month")
    if isinstance(v, (int, float)) and v > 0:
        return int(v)
    t = (o.get("pay") or "").lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k|l|lakh|lpa)?", t)
    if not m:
        return None
    n = float(m.group(1)) * {"k": 1e3, "l": 1e5, "lakh": 1e5, "lpa": 1e5 / 12}.get(m.group(2) or "", 1)
    return int(n) if n >= 1000 else None


def load(pattern="screen_*.json"):
    openings, rejected, round1, companies = [], [], [], []
    for f in sorted(glob.glob(os.path.join(HERE, pattern))):
        d = json.load(open(f, encoding="utf-8"))
        for o in d.get("openings", []):
            o["_cluster"] = d.get("cluster", os.path.basename(f))
            openings.append(o)
        rejected += d.get("rejected", [])
        round1 += d.get("round1", [])
        companies += d.get("companies", [])
    return openings, rejected, round1, companies


def build(sheet="main"):
    openings, rejected, round1, companies = load(SHEETS[sheet][0])
    vpath = os.path.join(HERE, "verify_links.json")
    verified = json.load(open(vpath)) if os.path.exists(vpath) else {}
    seen, jobs = {}, []
    for o in openings:
        k = (o.get("url") or "").split("?")[0].rstrip("/").lower()
        if not k or k in seen:
            continue
        seen[k] = 1
        if verified.get(o["url"], {}).get("ok") is False:
            rejected.append({"company": o["company"], "role": o["role"], "url": o["url"],
                             "reason": "closed on final link check: " + verified[o["url"]]["how"]})
            continue
        track = o.get("track") if o.get("track") in TIERS else "analyst"
        if sheet == "swe":
            track = "swe"
        if sheet == "startups":
            st = stipend(o)
            if st is not None and st < MIN_STIPEND:
                rejected.append({"company": o["company"], "role": o["role"], "url": o["url"],
                                 "reason": f"stipend ₹{st:,}/month is below ₹30,000"})
                continue
            if st is None:
                track = "nostip"
        dl = parse_date(o.get("deadline"))
        tier = "soon" if dl and 0 <= (dl - CHECKED).days <= SOON_DAYS else track
        if dl and dl < CHECKED:
            rejected.append({"company": o["company"], "role": o["role"], "url": o["url"], "reason": "deadline passed"})
            continue
        resume = "SDE" if sheet == "swe" else "DS / AI" if (o.get("track") == "ai") else "Analyst / PM"
        jid = str(o.get("job_id") or "")
        jobs.append({
            "id": slug(o["company"]) + "-" + (slug(jid) or slug(o["role"])),
            "tier": tier,
            "role": o["role"].strip(),
            "url": o["url"],
            "company": o["company"],
            "location": o.get("location", ""),
            "job_id": jid,
            "type": type_line(o),
            "exp": o.get("exp", ""),
            "pay": o.get("pay", "") or "",
            "jd": (o.get("jd", "") + (" Note: " + o["note"].strip() if (o.get("note") or "").strip() else "")).strip(),
            "li": o.get("li") or o["company"],
            "deadline": short_date(dl) if dl else "",
            "resume": resume,
            "_rank": int(o.get("city_rank") or 4),
            "_dl": dl or datetime.date(2100, 1, 1),
        })
    jobs.sort(key=lambda j: (ORDER.index(j["tier"]), j["_dl"] if j["tier"] == "soon" else 0, j["_rank"], j["company"].lower(), j["role"].lower()))
    # unique ids
    c = collections.Counter()
    for j in jobs:
        c[j["id"]] += 1
        if c[j["id"]] > 1:
            j["id"] += f"-{c[j['id']]}"
        j.pop("_rank"); j.pop("_dl")
    return jobs, rejected, round1, companies


def left_out_text(jobs, rejected, round1, companies):
    n_co = len({c.get("name") for c in companies})
    reasons = collections.Counter()
    for r in rejected:
        t = (r.get("reason") or "").lower()
        if "summer" in t or "penultimate" in t or "2028" in t:
            reasons["Summer 2027 / penultimate-year programmes"] += 1
        elif "sde" in t or "swe" in t or "software" in t or "engineering" in t:
            reasons["software-engineering interns with no data/AI/product angle"] += 1
        elif "master" in t or "mba" in t or "phd" in t or "postgrad" in t:
            reasons["needs a Master's, MBA or PhD"] += 1
        elif "deadline" in t or "closed" in t or "expired" in t:
            reasons["closed or past deadline"] += 1
        elif "graduat" in t or "batch" in t or "2025" in t or "2026" in t:
            reasons["for 2025/2026 graduates or already-graduated candidates"] += 1
        else:
            reasons["outside the role list (sales, HR, finance, ops, design, hardware…)"] += 1
    st = collections.Counter(r.get("status") for r in round1)
    s = (f"Crawled the careers sites of {n_co} employers, and swept Internshala for listings that state a stipend, "
         f"on 30–31 Oct 2026. Every link was checked against "
         f"the employer's own hiring API or job board on that day. Left out {len(rejected)} India internship postings: " +
         "; ".join(f"{v} {k}" for k, v in reasons.most_common()) + ". ")
    if round1:
        s += ("Round-1/2 search leads re-checked: " + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in st.most_common() if k) + ". ")
    s += "Stipend is blank where the posting does not state one."
    return s


def main():
    out = os.path.join(ROOT, "data", "applications-internships.js")
    files = {"main": out, "startups": out.replace(".js", "-startups.js"), "swe": out.replace(".js", "-swe.js")}
    blurbs = {
        "main": "off-campus internships (Nov 2026 – May 2027) at MNCs, banks, consulting firms and top Indian companies",
        "startups": "internships at well-funded startups and scale-ups paying ₹30,000+/month (or not stating a stipend)",
        "swe": "software-engineering internships in India, kept separately from the data/AI/product roles",
    }
    for sheet, (pattern, tab, order) in SHEETS.items():
        jobs, rejected, round1, companies = build(sheet)
        T = {
            "edition": "internships-2026-27" + ("" if sheet == "main" else "-" + sheet),
            "tab": tab, "order": order,
            "title": "Nov 2026 – May 2027",
            "checked": f"{CHECKED.day} {MONTHS[CHECKED.month - 1]} {CHECKED.year}",
            "exp_label": "Who can apply",
            "pay_label": "Stipend (₹/month)",
            "left_out": left_out_text(jobs, rejected, round1, companies) if companies or rejected else "Search in progress.",
            "tiers": {k: v for k, v in TIERS.items() if any(j["tier"] == k for j in jobs)},
            "jobs": jobs,
        }
        if sheet != "main":
            T["meta"] = f"{len(jobs)} live openings · every link rechecked {T['checked']}"
        head = (f"/* Internship tracker, sheet '{tab}': {blurbs[sheet]}.\n"
                f"   Built by data/raw/internships/build_internships.py from {pattern}. */\n")
        body = ("window.TRACKER_SHEETS = window.TRACKER_SHEETS || {};\n"
                f"window.TRACKER_SHEETS[{json.dumps(sheet)}] = " + json.dumps(T, ensure_ascii=False, indent=1) + ";\n")
        if sheet == "main":
            body += "window.TRACKER = window.TRACKER_SHEETS.main;\n"
        with open(files[sheet], "w", encoding="utf-8") as f:
            f.write(head + body)
        print(f"{sheet}: {len(jobs)} jobs -> {files[sheet]}", dict(collections.Counter(j["tier"] for j in jobs)))


if __name__ == "__main__":
    main()
