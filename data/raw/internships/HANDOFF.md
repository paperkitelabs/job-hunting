# Internship search — final state (31 Oct 2026)

The sheet is built and live: `applications-internships.html`, three tabs, 43 openings. Every link was
fetched against the employer's own hiring API or job board on 30–31 Oct 2026.

## What the candidate wanted
- B.Tech CSE (Data Science), final year, DJ Sanghvi College of Engineering, Mumbai. Graduates **May 2027**. Off-campus.
- **Window:** the internship must **start between now and Feb 2027** so the work falls inside Nov 2026 – May 2027.
  A May 2027 start is useless — that is when he graduates and can take a full-time job.
  Jan–Jun/Jul 2027 internships are included and flagged "runs past May".
- **Roles only:** PM / APM / product analyst, data analyst, business analyst, consultant / strategy,
  data science, AI/ML engineer, forward deployed engineer. Trainee, off-cycle and apprentice count.
- **Stipend:** for startups, **₹30,000/month is the floor**; ₹40,000+ is good. He has already done startup
  internships up to ₹25,000 and will not go below ₹30,000.
- **Location:** Mumbai > Pune > Bengaluru > other India > remote. In-office preferred.
- **Links:** the employer's own careers site, verified live. Internshala links are allowed **only** flagged
  "apply via Internshala", because it is the one source that states a stipend. Never LinkedIn, Naukri or Indeed.

## The three sheets
`tracker.js` reads `window.TRACKER_SHEETS`; `?sheet=<key>` picks one, and each keeps its own ticks.

| Tab | File | Rows | Source |
| --- | --- | --- | --- |
| MNCs & top companies | `data/applications-internships.js` | 28 | careers-API crawl of 241 employers |
| Startups (₹30k+ stipend) | `data/applications-internships-startups.js` | 7 | Internshala stipend sweep |
| Plain roles (software engineering) | `data/applications-internships-swe.js` | 8 | SWE rejects re-screened + Internshala |

## How it was built, and what each round was worth
1. **Rounds 1–2 (earlier sessions, no network):** search snippets only. 35 unverified "openings" and
   135 aggregator leads. Re-checked this round: 92 were not on the employers' sites at all, 12 closed, 8 live.
   Files `disc_*.json`, `list_*.txt`, superseded.
2. **Round 3 (this session):** 12 agents crawled all 284 companies on their own ATSs. 561 India intern/trainee
   postings found, every JD read, **26 kept**. Files `crawl-<company>.json`, `screen_<cluster>.json`.
3. **Round 4:** 306 more employers in `packs_r4/`. Three packs ran (global banks 2, Indian fintech, analytics/KPO)
   and yielded **3** openings; the other agents were stopped as not worth the cost. Five packs never ran:
   `R4b`, `R4f` ×2, `R4g` ×2, `R4h` ×2, `R4i` ×2.
4. **Internshala sweep:** `internshala_sweep.py` + `internshala_screen.py`. 1,870 live listings, only **32**
   at ₹30,000+/month, **9 kept** after screening and vetting.

### Why the MNC yield was low
Large MNCs and banks fill final-year Jan–Jun internships through **on-campus** drives, not their public careers
sites. What they post publicly in October is mostly full-time roles, degree-holder apprenticeships and
CA/MBA trainee programmes. Of 561 India intern postings, ~95% failed the screen: 117 wrong function
(HR, finance, sales, ops, design), 30 pure SWE, 30 for already-graduated candidates, 26 Master's/MBA/PhD only.
All 21 global investment banks: 44 postings, **0** fit.

### Why the stipend question is hard
Glassdoor and AmbitionBox both block automated access (403). Levels.fyi is open but holds only 254 India
intern records, mostly software/quant and from past years. Company career sites almost never state a stipend.
**Internshala states one on every listing**, which is why the startups tab comes from there.

## Tools in this folder
- `ats.py` — shared crawl helper: Workday (incl. the India facet and full paging), Greenhouse, Lever, Ashby,
  SmartRecruiters, Eightfold (both the v2 and PCSX APIs), Oracle Recruiting, amazon.jobs.
- `build_internships.py` — `screen*.json` → the three tracker files. Holds the tier order, city ranking,
  the ₹30,000 floor and the "closing soon" cutoff.
- `verify_links.py` — independent liveness check of every row; `build_internships.py` drops whatever fails.
- `internshala_sweep.py` / `internshala_screen.py` — the stipend source, including the hand-vetting list.
- `CRAWL_BRIEF.md` — the brief every crawl agent followed.

To refresh: `python3 data/raw/internships/verify_links.py && python3 data/raw/internships/build_internships.py`.

## If you pick this up again
1. **Re-run in late Nov and Dec.** Most Jan-start internships are posted then, and several employers said
   their programme was "not open yet".
2. **Employers that block automated access** and are worth checking by hand — Pune and Mumbai ones first:
   Persistent, KPIT (both Pune), TCS, Cognizant, LTIMindtree, ICICI Bank, ICICI Lombard, NSE, NPCI,
   Kotak Securities, Avendus, Piramal, LatentView, Zepto, Zomato/Blinkit, Ola, McKinsey, Bain, BNP Paribas, NatWest.
3. **Cheapest next step:** the user filters LinkedIn himself (Internship, India, past week) and pastes the
   job links; each one is then matched to the employer's own careers site and verified. No large crawl needed.
4. **Do not re-crawl** a company already covered in `crawl-*.json` — that ground is done.
