# Off-campus application list

A single static page holding every opening gathered and screened for an off-campus search —
data, AI, analytics and consulting roles in India for a May 2027 graduate.

No build step, no dependencies, no framework. Plain HTML, CSS and JavaScript.

## Run it locally

Open `index.html` in a browser. That is all — the data ships as JavaScript
(`data/jobs.js`, `data/companies.js`) so it works straight off the filesystem with no server.

If you prefer a server:

```
npx serve .
```

## Deploy

This folder lives **inside the `omkar-resume` repo**, so both hosts need to be told the site is
in a subdirectory — otherwise they look at the repo root and find no site.

**Vercel** — push to GitHub, then import the repo at [vercel.com/new](https://vercel.com/new) and set:

| Setting | Value |
| --- | --- |
| Framework preset | Other |
| **Root Directory** | `job-hunting` ← the part people forget |
| Build command | leave empty |
| Output directory | leave empty |

Or from the CLI, run it from inside this folder so it becomes the project root:

```
cd job-hunting
npx vercel
```

**GitHub Pages** — Pages cannot serve an arbitrary subfolder from `main`; it only offers `/` or
`/docs`. Either rename this folder to `docs`, or push it to its own repo, or just use Vercel.

## Files

```
applications-october.html   the application + referral tracker: September list rechecked 27 Oct
applications-november.html  same tracker, new openings from the 27 Oct search (data/applications-november.js)
data/applications-october.js its rows: summarized JD, LinkedIn referrer searches, resume to send
applications-internships.html internships only (Nov 2026 – May 2027), same tracker (data/applications-internships.js)
data/raw/internships/        company universe, agent brief, search results and HANDOFF.md for the internship sheet
tracker.js / tracker.css     shared by every applications-*.html page; ticks save in the browser
index.html          the full research list
styles.css          all styling
app.js              sorting, filtering, search, expand/collapse
data/jobs.json      161 openings — the data of record
data/jobs.js        same data as a <script> so it loads without a server
data/companies.json 62 employers with pay bands and off-campus openness
data/companies.js   same, as a script
```

## The data

Every row was gathered from the employer's own careers API — Amazon's search API,
Workday, Oracle Recruiting, Greenhouse, Lever, Ashby, SmartRecruiters and Zwayam —
rather than from a jobs aggregator. Each has:

- **match** — how closely the posted requirements line up with the resume
- **chance** — rough likelihood of getting through, from the stated experience bar,
  whether it is an internship, and how far the requirements sit above ~16–20 months
- **pay** — indicative India CTC band for that employer at that level
- **status** — `verified` (screened then adversarially re-checked with the link tested
  against the employer's hiring API), `screened`, `unscreened` (found in a crawl, read it
  yourself), or `rejected` (checked and ruled out, kept with the reason)

Roles that were checked and rejected are deliberately kept. Knowing why not to apply
saves as much time as the shortlist does.

## Updating it

Edit `data/jobs.json`, then regenerate the script copy:

```bash
python -c "import json;d=json.load(open('data/jobs.json',encoding='utf-8'));open('data/jobs.js','w',encoding='utf-8').write('window.JOBS='+json.dumps(d,ensure_ascii=False)+';')"
```

## Availability line

Use this wherever a form asks:

> Graduating May 2027, available full-time from June 2027; available for a full-time
> internship from January to May 2027.
