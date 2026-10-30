"""Builds data/applications-internships.js from the round-3 screen_*.json files in this folder.
Run from the repo root:  python3 data/raw/internships/build_internships.py
Reads screen_*.json (openings + rejected), dedups, assigns tiers, sorts by city preference, writes the tracker file."""
import json, glob, re, os, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHECKED = datetime.date(2026, 10, 30)
SOON_DAYS = 10
TIERS = {
    "soon": "Closing soon: apply this week",
    "bfsi": "Banks, financial services and insurance",
    "consult": "Consulting, Big 4 and analytics firms",
    "pm": "Product: APM, product analyst and PM interns",
    "analyst": "Data and business analyst interns, other companies",
    "ai": "Data science, AI/ML and forward deployed interns",
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


def load():
    openings, rejected, round1, companies = [], [], [], []
    for f in sorted(glob.glob(os.path.join(HERE, "screen_*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for o in d.get("openings", []):
            o["_cluster"] = d.get("cluster", os.path.basename(f))
            openings.append(o)
        rejected += d.get("rejected", [])
        round1 += d.get("round1", [])
        companies += d.get("companies", [])
    return openings, rejected, round1, companies


def build():
    openings, rejected, round1, companies = load()
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
        dl = parse_date(o.get("deadline"))
        tier = "soon" if dl and 0 <= (dl - CHECKED).days <= SOON_DAYS else track
        if dl and dl < CHECKED:
            rejected.append({"company": o["company"], "role": o["role"], "url": o["url"], "reason": "deadline passed"})
            continue
        resume = "DS / AI" if track == "ai" else "Analyst / PM"
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
            "jd": o.get("jd", ""),
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
    s = (f"Crawled the careers sites of {n_co} employers on {CHECKED.day} Oct {CHECKED.year}. Every link was checked against "
         f"the employer's own hiring API or job board on that day. Left out {len(rejected)} India internship postings: " +
         "; ".join(f"{v} {k}" for k, v in reasons.most_common()) + ". ")
    if round1:
        s += ("Round-1/2 search leads re-checked: " + ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in st.most_common() if k) + ". ")
    s += "Stipend is blank where the posting does not state one."
    return s


def main():
    jobs, rejected, round1, companies = build()
    T = {
        "edition": "internships-2026-27",
        "title": "Nov 2026 – May 2027",
        "checked": f"{CHECKED.day} Oct {CHECKED.year}",
        "exp_label": "Who can apply",
        "pay_label": "Stipend (₹/month)",
        "left_out": left_out_text(jobs, rejected, round1, companies),
        "tiers": {k: v for k, v in TIERS.items() if any(j["tier"] == k for j in jobs)},
        "jobs": jobs,
    }
    head = ("/* Internship edition of the application tracker: off-campus internships (Nov 2026 – May 2027) at MNCs,\n"
            "   banks, consulting firms and top Indian companies. Built by data/raw/internships/build_internships.py\n"
            "   from the round-3 careers-API crawl (screen_*.json). */\n")
    out = os.path.join(ROOT, "data", "applications-internships.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write(head + "window.TRACKER = " + json.dumps(T, ensure_ascii=False, indent=1) + ";\n")
    print(f"{len(jobs)} jobs -> {out}")
    print(collections.Counter(j["tier"] for j in jobs))


if __name__ == "__main__":
    main()
