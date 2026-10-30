"""Shared ATS crawl helpers for the internship search. Import with:
    import sys; sys.path.insert(0, '/home/user/job-hunting/data/raw/internships'); import ats
Every function returns a list of dicts: {title, loc, url, id, posted, desc(optional), raw(optional)}.
desc is plain text (HTML stripped). Use ats.is_india(), ats.is_intern() to filter.
"""
import json, re, time, html, urllib.parse
import requests

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
                  "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9"})
INTERN_QUERIES = ["intern", "internship", "trainee", "off-cycle", "apprentice"]
INDIA_WORDS = ["india", "mumbai", "pune", "bengaluru", "bangalore", "hyderabad", "chennai", "gurugram", "gurgaon",
               "noida", "delhi", "kolkata", "ahmedabad", "gift city", "gandhinagar", "jaipur", "kochi", "coimbatore",
               "thane", "navi mumbai", "vadodara", "indore", "chandigarh", "mohali", "trivandrum", "thiruvananthapuram",
               "mysore", "mysuru", "nagpur", "bhubaneswar", "lucknow", "goa", "vizag", "visakhapatnam", "surat"]
INDIA_RE = re.compile(r"\b(" + "|".join(INDIA_WORDS) + r"|ind|in-[a-z]{2})\b", re.I)
INTERN_RE = re.compile(r"\b(intern|interns|internship|trainee|off[- ]?cycle|apprentice|apprenticeship|co-?op|industrial training|winter analyst|summer analyst|stipend)\b", re.I)


def strip(h):
    if not h:
        return ""
    h = re.sub(r"<(br|p|li|div|h\d)[^>]*>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\xa0]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n", h).strip()


def is_india(*texts):
    return bool(INDIA_RE.search(" ".join(x for x in texts if x)))


def is_intern(*texts):
    return bool(INTERN_RE.search(" ".join(x for x in texts if x)))


def get(url, **kw):
    for i in range(3):
        try:
            r = S.get(url, timeout=kw.pop("timeout", 30), **kw)
            if r.status_code in (429, 502, 503):
                time.sleep(2 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(2 * (i + 1))
    return None


def post(url, payload, **kw):
    for i in range(3):
        try:
            r = S.post(url, json=payload, timeout=30, **kw)
            if r.status_code in (429, 502, 503):
                time.sleep(2 * (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(2 * (i + 1))
    return None


# ---------------- Workday ----------------
def _wd_parse(base_url):
    """'https://ms.wd5.myworkdayjobs.com/External' or '.../en-US/External' or cxs url -> (host, tenant, site)."""
    u = urllib.parse.urlparse(base_url)
    parts = [p for p in u.path.split("/") if p]
    if "cxs" in parts:
        i = parts.index("cxs"); return u.netloc, parts[i + 1], parts[i + 2]
    if parts and parts[0] == "recruiting":  # wd1.myworkdaysite.com/recruiting/<tenant>/<site>
        return u.netloc, parts[1], parts[2]
    parts = [p for p in parts if not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", p)]
    tenant = u.netloc.split(".")[0]
    return u.netloc, tenant, parts[0]


def workday(base_url, queries=INTERN_QUERIES, india_only=True, max_pages=15):
    host, tenant, site = _wd_parse(base_url)
    api = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    pub = f"https://{host}/{'recruiting/' + tenant + '/' if 'myworkdaysite' in host else ''}{site}"
    out, seen = [], set()
    facets = {}
    if india_only:  # find India country facet id
        r = post(api, {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
        if r is not None and r.ok:
            def walk(node, param):
                for v in node.get("values", []) or []:
                    p = v.get("facetParameter") or param
                    if v.get("descriptor", "").strip().lower() == "india" and param and "id" in v:
                        facets.setdefault(param, []).append(v["id"])
                    if v.get("values"):  # nested groups, e.g. locationMainGroup -> locations
                        walk(v, p)
            for f in r.json().get("facets", []):
                walk(f, f.get("facetParameter"))
        # keep only country-type facet if several
        for k in list(facets):
            if "country" in k.lower():
                facets = {k: facets[k]}; break
    for q in queries:
        total = None  # Workday returns total only on the first page
        for page in range(max_pages):
            r = post(api, {"appliedFacets": facets, "limit": 20, "offset": page * 20, "searchText": q})
            if r is None or not r.ok:
                break
            js = r.json(); posts = js.get("jobPostings", [])
            for p in posts:
                path = p.get("externalPath", "")
                if path in seen:
                    continue
                seen.add(path)
                out.append({"title": p.get("title"), "loc": p.get("locationsText"), "url": pub + path,
                            "id": (p.get("bulletFields") or [""])[0], "posted": p.get("postedOn"),
                            "api": f"https://{host}/wday/cxs/{tenant}/{site}{path}", "query": q})
            if total is None:
                total = js.get("total", 0)
            if len(posts) < 20 or (page + 1) * 20 >= total:
                break
    return out, {"api": api, "india_facet": facets}


def workday_detail(job):
    r = get(job["api"])
    if r is None or not r.ok:
        return None
    i = r.json().get("jobPostingInfo", {})
    return {"title": i.get("title"), "loc": ", ".join([i.get("location", "")] + (i.get("additionalLocations") or [])),
            "country": (i.get("country") or {}).get("descriptor"), "id": i.get("jobReqId"), "posted": i.get("startDate"),
            "end": i.get("endDate"), "time_type": i.get("timeType"), "can_apply": i.get("canApply"),
            "url": i.get("externalUrl") or job["url"], "desc": strip(i.get("jobDescription")), "status": r.status_code}


# ---------------- Greenhouse / Lever / Ashby / SmartRecruiters ----------------
def greenhouse(board):
    r = get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
    if r is None or not r.ok:
        return None
    return [{"title": j["title"], "loc": (j.get("location") or {}).get("name"), "url": j.get("absolute_url"),
             "id": str(j["id"]), "posted": j.get("updated_at"), "desc": strip(html.unescape(j.get("content", "")))}
            for j in r.json().get("jobs", [])]


def lever(co, eu=False):
    r = get(f"https://api.{'eu.' if eu else ''}lever.co/v0/postings/{co}?mode=json")
    if r is None or not r.ok:
        return None
    return [{"title": j["text"], "loc": (j.get("categories") or {}).get("location"), "url": j.get("hostedUrl"),
             "id": j["id"], "posted": j.get("createdAt"), "commitment": (j.get("categories") or {}).get("commitment"),
             "desc": strip(j.get("description", "")) + "\n" + "\n".join(strip(l.get("content", "")) for l in j.get("lists", []))}
            for j in r.json()]


def ashby(co):
    r = get(f"https://api.ashbyhq.com/posting-api/job-board/{co}?includeCompensation=true")
    if r is None or not r.ok:
        return None
    return [{"title": j["title"], "loc": j.get("location"), "url": j.get("jobUrl"), "id": j.get("id"),
             "posted": j.get("publishedAt"), "employment": j.get("employmentType"),
             "secondary": [s.get("location") for s in j.get("secondaryLocations", [])],
             "desc": j.get("descriptionPlain") or strip(j.get("descriptionHtml"))} for j in r.json().get("jobs", [])]


def smartrecruiters(co, queries=INTERN_QUERIES, country="in"):
    out, seen = [], set()
    for q in queries + [""]:
        off = 0
        while True:
            r = get(f"https://api.smartrecruiters.com/v1/companies/{co}/postings",
                    params={"q": q, "country": country, "limit": 100, "offset": off})
            if r is None or not r.ok:
                break
            js = r.json()
            for j in js.get("content", []):
                if j["id"] in seen:
                    continue
                seen.add(j["id"])
                loc = j.get("location", {})
                out.append({"title": j["name"], "loc": loc.get("fullLocation") or loc.get("city"),
                            "url": f"https://jobs.smartrecruiters.com/{co}/{j['id']}", "id": j["id"],
                            "ref": j.get("refNumber"), "posted": j.get("releasedDate"),
                            "api": f"https://api.smartrecruiters.com/v1/companies/{co}/postings/{j['id']}"})
            off += 100
            if off >= js.get("totalFound", 0) or q == "" and off >= 400:
                break
        if q == "" and len(out) > 300:
            break
    return out


def smartrecruiters_detail(job):
    r = get(job["api"])
    if r is None or not r.ok:
        return None
    j = r.json(); sec = (j.get("jobAd") or {}).get("sections", {})
    return {"title": j.get("name"), "active": j.get("active"), "url": j.get("postingUrl") or job["url"],
            "apply": j.get("applyUrl"), "desc": "\n".join(strip(v.get("text")) for v in sec.values() if isinstance(v, dict))}


# ---------------- Eightfold ----------------
def eightfold(host, domain, queries=INTERN_QUERIES, location="India"):
    """host e.g. 'paypal.eightfold.ai', domain e.g. 'paypal.com'."""
    out, seen = [], set()
    for q in queries:
        start = 0
        while start < 300:
            r = get(f"https://{host}/api/apply/v2/jobs", params={"domain": domain, "query": q, "location": location,
                                                                  "start": start, "num": 10, "sort_by": "relevance"})
            if r is None or not r.ok:
                break
            js = r.json(); pos = js.get("positions", [])
            for p in pos:
                if p["id"] in seen:
                    continue
                seen.add(p["id"])
                out.append({"title": p.get("name"), "loc": p.get("location"), "id": p.get("display_job_id") or p["id"],
                            "url": p.get("canonicalPositionUrl") or f"https://{host}/careers/job/{p['id']}?domain={domain}",
                            "posted": p.get("t_create"), "pid": p["id"],
                            "desc": strip(p.get("job_description", ""))})
            start += 10
            if len(pos) < 10:
                break
    return out


def eightfold_pcsx(host, domain, queries=INTERN_QUERIES + [""], locations=("India",)):
    """Newer Eightfold sites (PayPal etc.) answer /api/apply/v2 with 403 'Not authorized for PCSX'; use this.
    locations: facet strings as the site lists them, e.g. 'Bengaluru, KA, India' (see filterDef.facets.locations)."""
    out, seen = [], set()
    for loc in locations:
        for q in queries:
            start = 0
            while start < 500:
                r = get(f"https://{host}/api/pcsx/search", params={"domain": domain, "query": q, "location": loc, "start": start})
                if r is None or not r.ok:
                    break
                d = r.json().get("data", {}); pos = d.get("positions", [])
                for p in pos:
                    if p["id"] in seen:
                        continue
                    seen.add(p["id"])
                    out.append({"title": p.get("name"), "loc": "; ".join(p.get("locations", [])), "id": p.get("displayJobId"),
                                "pid": p["id"], "posted": p.get("postedTs"), "dept": p.get("department"),
                                "url": f"https://{host}{p.get('positionUrl')}?domain={domain}"})
                start += len(pos)
                if not pos or start >= d.get("count", 0):
                    break
    return out


def eightfold_pcsx_detail(host, domain, pid):
    r = get(f"https://{host}/api/pcsx/position_details", params={"position_id": pid, "domain": domain})
    if r is None or not r.ok:
        return None
    p = r.json().get("data", {})
    return {"title": p.get("name"), "loc": "; ".join(p.get("locations", [])), "desc": strip(p.get("jobDescription", "")),
            "status": r.status_code}


def eightfold_detail(host, domain, pid):
    r = get(f"https://{host}/api/apply/v2/jobs/{pid}", params={"domain": domain})
    if r is None or not r.ok:
        return None
    p = r.json()
    return {"title": p.get("name"), "loc": p.get("location"), "desc": strip(p.get("job_description", "")), "status": r.status_code}


# ---------------- Oracle Recruiting Cloud ----------------
ORACLE_INDIA = {"jpmc.fa.oraclecloud.com": 300000000289360}  # find others via locationsFacet (Name == 'India')


def oracle_india_id(host, site):
    r = get(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions",
            params={"onlyData": "true", "finder": f"findReqs;siteNumber={site},facetsList=LOCATIONS,limit=1"})
    try:
        for l in r.json()["items"][0].get("locationsFacet", []):
            if l["Name"].strip() == "India":
                return l["Id"]
    except Exception:
        return None


def oracle(host, site, queries=INTERN_QUERIES, location_id=None):
    """host e.g. 'jpmc.fa.oraclecloud.com', site e.g. 'CX_1001'. location_id = India location id if known
    (found via the facet list in the response, 'locationsFacet')."""
    out, seen = [], set()
    for q in queries:
        off = 0
        while off < 500:
            finder = f"findReqs;siteNumber={site},facetsList=LOCATIONS;TITLES,limit=25,offset={off},keyword=\"{q}\""
            if location_id:
                finder += f",locationId={location_id}"
            r = get(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions",
                    params={"onlyData": "true", "expand": "requisitionList.secondaryLocations", "finder": finder})
            if r is None or not r.ok:
                break
            items = r.json().get("items", [])
            if not items:
                break
            reqs = items[0].get("requisitionList", [])
            for j in reqs:
                if j["Id"] in seen:
                    continue
                seen.add(j["Id"])
                locs = [j.get("PrimaryLocation", "")] + [s.get("Name", "") for s in j.get("secondaryLocations", [])]
                out.append({"title": j.get("Title"), "loc": "; ".join(l for l in locs if l), "id": j["Id"],
                            "posted": j.get("PostedDate"),
                            "url": f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{j['Id']}",
                            "short": j.get("ShortDescriptionStr")})
            off += 25
            if len(reqs) < 25:
                break
    return out


def oracle_detail(host, site, jid):
    r = get(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails",
            params={"expand": "all", "onlyData": "true", "finder": f"ById;Id=\"{jid}\",siteNumber={site}"})
    if r is None or not r.ok or not r.json().get("items"):
        return None
    j = r.json()["items"][0]
    return {"title": j.get("Title"), "loc": j.get("PrimaryLocation"), "posted": j.get("ExternalPostedStartDate"),
            "end": j.get("ExternalPostedEndDate"),
            "desc": strip((j.get("ExternalDescriptionStr") or "") + "\n" + (j.get("ExternalResponsibilitiesStr") or "") +
                          "\n" + (j.get("ExternalQualificationsStr") or ""))}


# ---------------- Amazon ----------------
def amazon(queries=("intern", "internship", "trainee", "")):
    """country=IND. query '' pages through ALL India postings (~2,100) - filter them with is_intern()."""
    out, seen = [], set()
    for q in queries:
        off = 0
        while off < 1000:
            r = get("https://www.amazon.jobs/en/search.json", params={"base_query": q, "country": "IND", "result_limit": 100,
                                                                      "offset": off, "sort": "recent"})
            if r is None or not r.ok:
                break
            js = r.json(); jobs = js.get("jobs", [])
            for j in jobs:
                if j["id_icims"] in seen:
                    continue
                seen.add(j["id_icims"])
                out.append({"title": j["title"], "loc": j.get("normalized_location") or j.get("location"),
                            "url": "https://www.amazon.jobs" + j["job_path"], "id": j["id_icims"], "posted": j.get("posted_date"),
                            "desc": strip(j.get("description", "")) + "\nBASIC: " + strip(j.get("basic_qualifications", "")) +
                                    "\nPREFERRED: " + strip(j.get("preferred_qualifications", ""))})
            off += 100
            if off >= js.get("hits", 0):
                break
    return out


def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
