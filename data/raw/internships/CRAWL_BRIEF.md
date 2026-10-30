# Round-3 crawl brief (30 Oct 2026, full network access)

Round 1 and round 2 worked from search snippets only. This round queries each employer's own careers API directly,
verifies every link live, and reads every JD. Each agent covers one cluster.

## The candidate (screening rules)
- B.Tech CSE (Data Science), final year, DJ Sanghvi College of Engineering, Mumbai. Graduates **May 2027**. Off-campus.
- **Window:** the internship must run between Nov 2026 and May 2027. Any length.
  - Jan–Jun/Jul 2027 internships: **include**, and set `runs_past_may: true`.
  - Dates not stated, but posted recently for current students or 2027 grads: include, and note "dates not stated".
- **Exclude:**
  - Summer 2027 programmes for penultimate-year students (May/Jun–Jul/Aug 2027, "returning to studies", "2028 graduates").
  - Postings for 2025/2026 graduates only.
  - Postings that need a Master's, MBA or PhD, or that need a degree already completed (e.g. NATS graduate apprentices).
- **Roles, only these:**
  - PM / APM / product analyst intern.
  - Data analyst intern.
  - Business analyst intern.
  - Consultant / strategy / analyst intern (consulting, banking analytics, risk analytics).
  - Data science intern.
  - AI/ML engineer intern (incl. GenAI, applied scientist, quant research/analytics).
  - Forward deployed engineer intern.
  - Synonyms count: trainee, off-cycle, winter intern, industrial trainee, apprentice, co-op, "graduate intern".
- **Reject**, but list them with a reason:
  - Pure SWE/SDE interns with no data/AI/product angle.
  - Sales, HR, marketing, finance/accounting/CA/audit-only, legal, design, ops-only, hardware/VLSI/embedded.
- **Location:** India only (any city) or remote-India. `city_rank`: 1 Mumbai/Navi Mumbai/Thane, 2 Pune,
  3 Bengaluru, 4 other Indian city, 5 remote.

## Links
The apply link must be on the employer's own careers site or ATS, and must be **verified live** by you this session:
- detail API returns 200 and the posting is open, or
- the posting appears in the board's live list.

Never use LinkedIn, Naukri, Indeed, Internshala, Unstop or other aggregators.

## How to crawl
- Shared helper:
  `import sys; sys.path.insert(0, '/home/user/job-hunting/data/raw/internships'); import ats`. Read `ats.py` (same folder) first; the docstrings explain it.
- What the helper covers:
  - **Workday:** `ats.workday(url, queries)` + `ats.workday_detail(job)`. It auto-applies the India country facet.
    "N Locations" rows need the detail call.
  - **Greenhouse / Lever / Ashby:** `ats.greenhouse(board)`, `ats.lever(co)` (`eu=True` for EU), `ats.ashby(co)`.
    These return the whole board; filter with `ats.is_india` and `ats.is_intern`.
  - **SmartRecruiters:** `ats.smartrecruiters(co)` + `_detail`.
  - **Eightfold:** `ats.eightfold(...)`. If it answers 403 "Not authorized for PCSX", use `ats.eightfold_pcsx(...)` + `_detail`.
  - **Oracle:** `ats.oracle(host, site, queries, location_id=ats.oracle_india_id(host, site))` + `ats.oracle_detail`.
  - **Amazon:** `ats.amazon()`. Query "" pages through all India postings; filter the intern ones.
- Anything else, work out the site's JSON/HTML yourself: Phenom `.../api/jobs` or `/widgets`, SuccessFactors
  `career?company=..`, Taleo, iCIMS, BrassRing, Zwayam, Darwinbox, Keka, custom (Google, Microsoft, Goldman higher.gs.com…).
  Open the careers page HTML and look for the XHR endpoint.
- Known tenants and URLs from earlier crawls:
  - grep `data/raw/*.json` and `data/jobs.json` in the repo (job URLs reveal the ATS host/tenant/site).
  - each company's `round_notes` in your pack.
- Queries: intern, internship, trainee, off-cycle, apprentice, plus "analyst intern", "data", "2027" where search is fuzzy.
  For small boards, take the whole board.
- **WebSearch:** use it only to find a company's ATS/careers endpoint when nothing else works. **Max 8 searches per
  agent**, standard mode. Never use an aggregator result as a link.
- Be polite: sequential requests, at most a few per second.

## Round-1/2 items
Your pack lists each company's `round1_openings` and `round1_leads`.
- For every opening: check its URL/job id against the live API.
- For every lead: look for the same role on the careers site.
- Record each in `round1` with its status: `live`, `closed`, `not_found` or `matched` (+ new_url).

## Outputs (write into /home/user/job-hunting/data/raw/internships/)
1. `crawl-<company-slug>.json`, one per company crawled, holding the raw evidence:
   `{company, ats, endpoint, queried_at, queries, total_hits, india_intern_hits:[{title, loc, url, id, posted}], details:{<url>: <detail dict incl. full desc>}}`.
   Keep it to intern/trainee hits plus the details you fetched; don't dump thousands of unrelated postings.
2. `screen_<cluster>.json`:
```
{"cluster": "", "checked": "30 Oct 2026",
 "openings": [{"company":"", "role":"<exact posted title>", "url":"<verified careers URL>", "location":"<city>", "city_rank":1,
   "job_id":"", "duration":"6 months|not stated", "dates":"Jan–Jun 2027|not stated", "runs_past_may":false,
   "exp":"who can apply, as posted (e.g. final-year B.Tech students graduating 2027)",
   "pay":"₹40,000/month if stated else ''", "track":"bfsi|consult|pm|analyst|ai",
   "posted":"YYYY-MM-DD", "deadline":"YYYY-MM-DD or ''",
   "jd":"2–3 sentences, facts only: what the intern does + skills asked",
   "li":"<Company> <team name>", "resume":"Analyst / PM|DS / AI",
   "verified":"how you checked it live (e.g. Workday detail 200, canApply true)", "note":"anything to flag, or ''"}],
 "rejected": [{"company":"", "role":"", "url":"", "reason":""}],
 "round1": [{"company":"", "role":"", "old_url":"", "status":"live|closed|not_found|matched", "new_url":"", "note":""}],
 "companies": [{"name":"", "ats":"", "endpoint":"", "india_intern_hits":0, "kept":0, "note":""}]}
```
- `track`:
  - `ai` = data science / ML / AI / FDE / quant research.
  - `bfsi` = analyst roles at banks, financial firms and insurers.
  - `consult` = consulting firms and Big 4.
  - `pm` = product roles.
  - `analyst` = analyst roles elsewhere.
- `resume` is "DS / AI" for the `ai` track, else "Analyst / PM".
- Cover **every** company in your pack in `companies`, even when you found none, with the reason
  (e.g. "Workday India: 0 intern postings", "careers site has no API; checked HTML listing").
- Write valid JSON with python `json.dump(..., ensure_ascii=False, indent=1)`.
- Do **not** git commit. The lead session commits.
- Reply in ≤6 lines: counts (companies crawled, India intern hits, kept, rejected, round-1 statuses) and any
  companies you could not reach.
