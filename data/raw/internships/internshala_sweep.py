"""Sweeps Internshala for internships that state a stipend of at least MIN_STIPEND a month.

Internshala is the one source that publishes a stipend on every listing, so it is where the
"Startups (₹30k+ stipend)" sheet comes from. Run from the repo root:

    python3 data/raw/internships/internshala_sweep.py

Writes crawl-internshala.json (every ₹30k+ card found) and a shortlist the screening step reads.
Listing pages are paged per category; each card carries company, title, location, stipend and duration.
"""
import json, os, re, sys, time, html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ats  # noqa: E402

MIN_STIPEND = 30000
CATEGORIES = [
    "data-science", "data-analytics", "machine-learning", "artificial-intelligence-ai",
    "business-analytics", "product-management", "business-development", "operations",
    "consulting", "finance", "research", "software-development", "computer-science",
    "full-stack-development", "backend-development", "frontend-development",
]
# Location slugs: Internshala paths look like /internships/<category>-internship-in-<city>/
CITIES = ["mumbai", "pune", "bangalore", "hyderabad", "delhi", "gurgaon", "noida", "chennai"]
PAGES = 6  # cards per page is ~40; six pages per category is plenty at this stipend level

CARD = re.compile(r'<div class="container-fluid individual_internship.*?(?=<div class="container-fluid individual_internship|<div id="scroll_to_top)', re.S)


def text(pattern, blob, default=""):
    m = re.search(pattern, blob, re.S)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else default


def parse_stipend(s):
    """'₹ 40,000 - 60,000 /month' -> (40000, 'month'). Returns (lowest number, unit) or (None, '')."""
    t = s.lower().replace(",", "").replace("₹", " ")
    unit = "month" if "/month" in t or "per month" in t else "lump" if "lump" in t else ""
    nums = [int(float(x)) for x in re.findall(r"(\d+(?:\.\d+)?)", t)]
    nums = [n for n in nums if n >= 500]
    return (min(nums) if nums else None, unit)


def cards(blob):
    for c in CARD.findall(blob):
        iid = text(r'internshipId="(\d+)"', c)
        if not iid:
            continue
        stip = text(r"<span class='stipend'>(.*?)</span>", c) or text(r'<span class="stipend">(.*?)</span>', c)
        low, unit = parse_stipend(stip)
        href = text(r'data-href=\'([^\']+)\'', c) or text(r'href="(/internship/detail/[^"]+)"', c)
        yield {
            "id": iid,
            "title": text(r'id="job_title"[^>]*>(.*?)</a>', c),
            "company": text(r'<p class="company-name">(.*?)</p>', c),
            "location": text(r'class="row-1-item locations">.*?<span>\s*<a[^>]*>(.*?)</a>', c),
            "stipend_text": stip,
            "stipend_inr_month": low if unit == "month" else None,
            "duration": text(r'<i class="ic-16-calendar"></i>\s*<span>(.*?)</span>', c),
            "posted": text(r'class="status-(?:inactive|success)"><i[^>]*></i><span>(.*?)</span>', c),
            "start": text(r'Starts (?:immediately|on) ?([^<]*)', c) or ("immediately" if "Starts immediately" in c else ""),
            "url": "https://internshala.com" + href if href.startswith("/") else href,
            "about": text(r'class="about_job">.*?<div class="text">(.*?)</div>', c),
            "skills": ", ".join(re.findall(r"<div class='job_skill'>(.*?)</div>", c)),
        }


def sweep():
    out, seen = [], set()
    paths = [f"/internships/{c}-internship/" for c in CATEGORIES]
    paths += [f"/internships/{c}-internship-in-{city}/" for c in ("data-science", "data-analytics", "product-management") for city in CITIES]
    for path in paths:
        for page in range(1, PAGES + 1):
            url = f"https://internshala.com{path}" + (f"page-{page}/" if page > 1 else "")
            r = ats.get(url, headers={"Accept": "text/html"})
            if r is None or r.status_code != 200:
                break
            found = 0
            for c in cards(r.text):
                found += 1
                if c["id"] in seen:
                    continue
                seen.add(c["id"])
                c["source_path"] = path
                out.append(c)
            print(f"  {path} p{page}: {found} cards, {len(out)} unique so far", flush=True)
            if found == 0:
                break
            time.sleep(0.6)
    return out


def main():
    allc = sweep()
    rich = [c for c in allc if (c["stipend_inr_month"] or 0) >= MIN_STIPEND]
    ats.save(os.path.join(HERE, "crawl-internshala.json"),
             {"source": "internshala.com", "checked": "30 Oct 2026", "min_stipend": MIN_STIPEND,
              "cards_seen": len(allc), "cards_at_or_above_min": len(rich), "cards": rich})
    print(f"\n{len(allc)} cards seen, {len(rich)} at ≥ ₹{MIN_STIPEND:,}/month")
    for c in sorted(rich, key=lambda x: -x["stipend_inr_month"])[:40]:
        print(f"  ₹{c['stipend_inr_month']:>7,} {c['company'][:28]:28} {c['title'][:42]:42} {c['location'][:18]:18} {c['duration']} | {c['start']}")


if __name__ == "__main__":
    main()
