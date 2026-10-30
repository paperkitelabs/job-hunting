# Internship discovery brief (shared by every agent)

Today is 30 Oct 2026. You are finding LIVE internship openings for one candidate:
- B.Tech CSE (Data Science), final year, DJ Sanghvi College of Engineering, Mumbai; graduates May 2027.
- Off-campus. Wants an internship whose work falls between Nov 2026 and May 2027
  (any length: 2, 3, 4, 6 months all fine). Jan–Jun/Jul 2027 internships are ALSO wanted —
  include them but set "overrun" to say it runs past May.
- Location preference: Mumbai > Pune > Bengaluru > other Indian cities > remote (India). In-office preferred.
- Roles wanted ONLY: Product Manager / APM / Product Analyst intern; Data Analyst intern;
  Business Analyst intern; Consultant / Strategy / Analyst intern (consulting, banking analytics, risk analytics);
  Data Science intern; AI/ML Engineer intern (incl. GenAI, applied scientist, quant research/analytics intern);
  Forward Deployed Engineer intern. Synonyms count: "trainee", "off-cycle intern", "winter intern",
  "industrial trainee", "apprentice", "co-op", "Intern - Analytics", "Graduate Intern", "January 2027 intern".
- NOT wanted: pure software-engineering/SDE interns with no data/AI/product angle, sales, HR, marketing,
  finance/accounting/CA, legal, design, ops-only, hardware/VLSI. Not wanted: Summer Internship 2027
  programmes meant for penultimate-year students (May–Jul 2027, "must return to studies") — list those under
  "excluded" with the reason, don't put them in "openings".

## What counts as a valid link
The application link MUST be on the company's own careers site or its ATS (e.g. *.myworkdayjobs.com,
*.oraclecloud.com, careers.<company>.com, jobs.lever.co/<co>, boards.greenhouse.io/<co>, job-boards.greenhouse.io,
jobs.ashbyhq.com/<co>, jobs.smartrecruiters.com/<co>, *.eightfold.ai, *.tal.net, *.successfactors.com,
*.taleo.net, *.icims.com, *.phenompeople / careers.<co>.com/job/...). NEVER LinkedIn, Indeed, Naukri,
Internshala, Glassdoor, Unstop, Prosple, Foundit, Instahyre, weekday, cutshort, or any blog/aggregator.
You MAY use those to discover openings — then search for the same job on the company careers site
(search the job title + company + "careers" / the job ID, or use site: queries) and record the careers link.
If you can only find it on an aggregator, put it in "leads" (with the aggregator URL as evidence and the
company's careers search page as careers_url) — never in "openings".

## Tools
- WebSearch works. Use many queries per company: e.g.
  `"<company>" intern India 2026`, `"<company>" internship data science India`, `site:<careers-domain> intern`,
  `"<company>" "off-cycle" OR "winter" intern India`, `"<company>" analyst intern Mumbai`, `"<company>" trainee data analytics 2027`,
  and role-wise queries ("product manager intern", "business analyst intern", "AI intern", "forward deployed").
  Prefer mode "standard"; use "extended" for companies where standard returns nothing useful but you expect openings.
- WebFetch and curl are mostly BLOCKED in this session (careers hosts fail DNS / 403). Try WebFetch at most once
  overall; if it fails, don't retry — rely on search results and their snippets.
- Liveness: we cannot open pages yet. Use signals from search: posted date, "apply by", "closing date",
  "no longer accepting", cohort year. Drop anything clearly closed or for 2025/2026-summer cohorts. A later step
  will check every link against the employer's careers API, so record the exact URL and job ID.

## Output — write ONE JSON file at the path given in your task
{
 "cluster": "...",
 "openings": [ {
   "company": "", "role": "<exact posted title>", "url": "<careers-site job URL>",
   "location": "", "job_id": "", "type": "Internship",
   "duration": "e.g. 6 months, Jan–Jun 2027 / not stated", "overrun": "" or "runs to Jun 2027",
   "exp": "who may apply, as posted (e.g. final-year students, 2027 grads)",
   "track": "pm|analyst|consult|bfsi|ai",   // ai = data science / ML / AI / FDE
   "posted": "date if known", "deadline": "date if known",
   "jd": "2–3 sentence summary of the posted JD: what the intern does + skills asked. Facts only.",
   "evidence": "where you saw it (search result title/snippet, URL) and why you think it is live",
   "confidence": "high|medium|low"
 } ],
 "leads": [ {"company":"", "role":"", "aggregator_url":"", "careers_url":"", "note":""} ],
 "excluded": [ {"company":"", "role":"", "url":"", "reason":""} ],
 "companies": [ {"name":"", "careers_url":"<best careers/early-careers/students page on the company domain>",
                 "ats":"workday|oracle|greenhouse|lever|ashby|smartrecruiters|eightfold|successfactors|taleo|phenom|other",
                 "ats_endpoint":"e.g. https://ms.wd5.myworkdayjobs.com/wday/cxs/ms/External/jobs if known",
                 "result":"found N | none found | programme not open yet", "note":"e.g. runs a Jan–Jun off-cycle programme; opens in Dec"} ]
}
Cover EVERY company in your list in "companies" (even when none found). Be exhaustive — the goal is the
maximum number of genuine openings. Do not invent URLs or job IDs: only record a URL you actually saw in a search
result. Write valid JSON (use python to json.dump if unsure). Then reply with a 3-line summary (counts).

## Round-2 lessons (read these first)
- Search budget is SHARED and small (~200 searches per turn across all agents). Spend it well: aim for
  ~2–3 searches per company, never more than 4. Put the company's highest-yield query first.
- `site:` in the query text does NOT restrict results. Use the WebSearch `allowed_domains` parameter set to the
  careers/ATS domain (e.g. ["careers.mastercard.com"], ["pgcareers.com"], ["myworkdayjobs.com"], ["jobs.lever.co"],
  ["job-boards.greenhouse.io","boards.greenhouse.io"], ["jobs.ashbyhq.com"]) with a query like
  "<company> intern India data" — this reliably returns real careers-site job URLs.
- myinternships.in listings are templated / unreliable — don't record them even as leads.
- Do not try WebFetch or curl at all (blocked).
