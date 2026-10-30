# Internship search — handoff (state as of 30 Oct 2026)

## What the user wants
A new tracker sheet, same format as `applications-october.html` / `applications-november.html`, holding only
**internships**:

- **Candidate:** B.Tech CSE (Data Science), final year, DJ Sanghvi College of Engineering, Mumbai. Graduates May 2027.
  Searching off-campus.
- **Window:** the work must fall between Nov 2026 and May 2027. Any length is fine (2, 3, 4 or 6 months).
  - Jan–Jun/Jul 2027 internships are **included** (the user chose this), flagged "runs past May".
  - Summer 2027 programmes for penultimate-year students are excluded.
- **Employers:** MNCs, Fortune 500, top Indian companies, global banks, consulting firms. Any office in India,
  HQ or branch.
- **Location order:** Mumbai > Pune > Bengaluru > other Indian cities > remote. In-office is preferred.
- **Roles, only these:** product manager / APM / product analyst intern, data analyst intern, business analyst intern,
  consultant / strategy intern, data science intern, AI/ML engineer intern, forward deployed engineer intern.
  "Trainee" and "off-cycle" synonyms count.
- **Links:** the company's own careers site or ATS only, **verified live**. Never LinkedIn, Indeed, Naukri or other
  aggregators. Those can be used to discover openings, but every row must link to the employer's careers site.
- **Coverage:** maximum. 284 companies are listed in `companies.json`.

## What exists
- `applications-internships.html`: page built, linked from the October and November pages.
  - Columns: "Who can apply" instead of "Experience asked", and "Stipend ₹/month" instead of pay.
  - Footer carries the availability line and the "runs past May" note.
- `data/applications-internships.js`: **placeholder, jobs = []**. Fill it.
- `tracker.js`: CSV headers now read `T.exp_label` and `T.pay_label`.
- `data/raw/internships/`:
  - `companies.json`: 284 companies in clusters A–K, each with a careers hint.
  - `BRIEF.md`: agent brief, including round-2 lessons.
  - `disc_<cluster>.json`: round-1 results.
    - 23 "openings" with a careers-site URL, but **not verified live** and mostly low confidence.
    - 130 aggregator "leads".
    - 103 "excluded".
    - Per-company careers URL, ATS and endpoint notes.
  - `disc_R2*.json`: round-2 results for 64 priority companies (all 4 batches complete, 12 low/medium-confidence openings). Lists are in
    `list_R2*.txt`. Each agent noted ATS endpoints and corrected careers URLs in its file.
  - `unsearched_after_r2.json`: 132 companies never searched at all.

## Why round 1 was thin
The old session had **no network access to careers sites**: Workday, Greenhouse, amazon.jobs and similar hosts were
all 403 / DNS blocked. It also had a **shared WebSearch budget of about 200 per turn** across all agents. So
everything came from search snippets, and most companies went unsearched.

The new session has **full network access**, which changes the method. **Crawl each employer's careers API
directly** with curl or python, the way the October and November data was built (see `data/raw/*.json` from earlier
crawls). Use WebSearch only to find a company's ATS, or for companies with custom career sites.

## Next steps
1. **Confirm network:**
   `curl -s -X POST -H 'Content-Type: application/json' -d '{"appliedFacets":{},"limit":20,"offset":0,"searchText":"intern"}' https://statestreet.wd1.myworkdayjobs.com/wday/cxs/statestreet/Global/jobs`
2. **Crawl, in parallel agents (about 8–12, by cluster).** Query every company's ATS for intern / trainee /
   "off-cycle" / apprentice postings in India. Endpoints:
   - **Workday:** `POST https://<t>.wd<N>.myworkdayjobs.com/wday/cxs/<t>/<site>/jobs` with searchText
     "intern" (also try "trainee", "internship").
     - Detail: `GET .../wday/cxs/<t>/<site>/job/<externalPath>`.
     - Filter to India via the locations facet or the text.
   - **Greenhouse:** `https://boards-api.greenhouse.io/v1/boards/<board>/jobs?content=true`
   - **Lever:** `https://api.lever.co/v0/postings/<co>?mode=json`
   - **Ashby:** `https://api.ashbyhq.com/posting-api/job-board/<co>`
   - **SmartRecruiters:** `https://api.smartrecruiters.com/v1/companies/<co>/postings?q=intern&country=in`
   - **Oracle Recruiting (JPMC, Amex):**
     `/hcmRestApi/resources/latest/recruitingCEJobRequisitions?finder=findReqs;siteNumber=<site>,keyword=intern,locationId=...`
   - **Eightfold (PayPal, BNY):** `https://<co>.eightfold.ai/api/apply/v2/jobs?domain=<co>.com&query=intern&location=India`
   - **Amazon:** `https://www.amazon.jobs/en/search.json?base_query=intern&country=IND&result_limit=100`
   - **Others:** Google, Microsoft, Phenom-based sites (pgcareers, careers.philips, careers.mastercard…) and
     SuccessFactors (Deloitte South Asia, StanChart) have JSON or HTML search pages. Fetch them.
   - Save every raw crawl to `data/raw/internships/crawl-<company>.json`.
3. **Re-verify** the 23 round-1 openings, and try to match the 130 leads to real careers-site postings.
   - Drop anything closed, expired, or for the wrong cohort.
   - Deloitte South Asia job-URL ids rise over time: about 545xxxxx was Apr 2026, about 587xxxxx+ was Sep–Oct 2026.
4. **Screen** each live posting against the role list, the window and India location, and read the full JD.
   Keep the rejects with a reason for `left_out`.
5. **Build `data/applications-internships.js`** in the same schema as `data/applications-november.js`.
   - Job fields: `id, tier, role, url, company, location, job_id, type, exp, pay, jd, li, deadline, resume`.
   - `type`: e.g. `"Internship · 6 mo, Jan–Jun 2027 · runs past May"`.
   - `exp`: who can apply.
   - `pay`: stipend if stated, else "".
   - `jd`: a 2–3 sentence summary of the posted JD.
   - `li`: LinkedIn people-search keywords: company + team.
   - `resume`: `"Analyst / PM"` or `"DS / AI"`. Tier `"ai"` drives the DS & AI filter in tracker.js.
   - Tiers, in this order: `soon` (closing within ~10 days), `bfsi`, `consult`, `pm`, `analyst`, `ai`.
     Within each tier, sort by city preference: Mumbai, Pune, Bengaluru, others, remote.
   - Set `checked` to the verification date and write `left_out`.
6. **Update `README.md`** (files list) and commit. Push to the session's designated branch.
