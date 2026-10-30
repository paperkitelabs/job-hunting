"""Final liveness pass over every opening in screen_*.json, independent of the crawl agents' own checks.
Run from the repo root:  python3 data/raw/internships/verify_links.py
Writes verify_links.json here: {url: {"ok": bool, "how": str}}. build_internships.py drops rows whose ok is False."""
import json, glob, os, re, sys, urllib.parse
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ats  # noqa: E402

AGG = re.compile(r"linkedin|naukri|indeed|internshala|glassdoor|unstop|foundit|instahyre|cutshort|weekday|prosple", re.I)


def check(url):
    if AGG.search(urllib.parse.urlparse(url).netloc):
        return {"ok": False, "how": "aggregator link"}
    u = urllib.parse.urlparse(url)
    try:
        if "myworkdayjobs.com" in u.netloc or "myworkdaysite.com" in u.netloc:
            parts = [p for p in u.path.split("/") if p and not re.fullmatch(r"[a-z]{2}-[A-Z]{2}", p)]
            if parts[0] == "recruiting":
                tenant, site, rest = parts[1], parts[2], parts[3:]
            else:
                tenant, site, rest = u.netloc.split(".")[0], parts[0], parts[1:]
            api = f"https://{u.netloc}/wday/cxs/{tenant}/{site}/" + "/".join(rest)
            r = ats.get(api)
            if r is None:
                return {"ok": None, "how": "workday: no response"}
            if r.status_code != 200:
                return {"ok": False, "how": f"workday detail {r.status_code}"}
            info = r.json().get("jobPostingInfo", {})
            return {"ok": bool(info.get("canApply", True)), "how": f"workday detail 200, canApply={info.get('canApply')}"}
        m = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([^/?]+)/jobs/(\d+)", url)
        if m:
            r = ats.get(f"https://boards-api.greenhouse.io/v1/boards/{m.group(1)}/jobs/{m.group(2)}")
            return {"ok": r is not None and r.status_code == 200, "how": f"greenhouse api {getattr(r, 'status_code', None)}"}
        m = re.search(r"jobs\.(eu\.)?lever\.co/([^/]+)/([0-9a-f-]{36})", url)
        if m:
            r = ats.get(f"https://api.{m.group(1) or ''}lever.co/v0/postings/{m.group(2)}/{m.group(3)}")
            return {"ok": r is not None and r.status_code == 200, "how": f"lever api {getattr(r, 'status_code', None)}"}
        m = re.search(r"jobs\.ashbyhq\.com/([^/]+)/([0-9a-f-]{36})", url)
        if m:
            jobs = ats.ashby(m.group(1)) or []
            return {"ok": any(m.group(2) in (j.get("url") or "") or j.get("id") == m.group(2) for j in jobs), "how": "ashby board list"}
        m = re.search(r"jobs\.smartrecruiters\.com/([^/]+)/(\d+)", url)
        if m:
            r = ats.get(f"https://api.smartrecruiters.com/v1/companies/{m.group(1)}/postings/{m.group(2)}")
            ok = r is not None and r.status_code == 200 and r.json().get("active", True)
            return {"ok": ok, "how": f"smartrecruiters api {getattr(r, 'status_code', None)}"}
        m = re.search(r"(\w[\w.-]*oraclecloud\.com)/hcmUI/CandidateExperience/[a-z]+/sites/([^/]+)/(?:job|requisitions/preview)/(\d+)", url)
        if m:
            d = ats.oracle_detail(m.group(1), m.group(2), m.group(3))
            return {"ok": d is not None, "how": "oracle detail " + ("found" if d else "missing")}
        m = re.search(r"amazon\.jobs/[a-z]+/jobs/(\d+)", url)
        if m:
            r = ats.get(f"https://www.amazon.jobs/en/jobs/{m.group(1)}")
            ok = r is not None and r.status_code == 200 and "no longer available" not in r.text.lower()
            return {"ok": ok, "how": f"amazon page {getattr(r, 'status_code', None)}"}
        r = ats.get(url, allow_redirects=True)
        if r is None:
            return {"ok": None, "how": "no response"}
        body = r.text.lower()
        dead = any(p in body for p in ["no longer accepting", "job is no longer available", "position has been filled",
                                        "this job has expired", "posting has expired", "job not found", "no longer available"])
        return {"ok": r.status_code == 200 and not dead, "how": f"GET {r.status_code}{' (closed text)' if dead else ''}"}
    except Exception as e:  # keep going on odd sites
        return {"ok": None, "how": f"error {type(e).__name__}"}


def main():
    urls = []
    for f in sorted(glob.glob(os.path.join(HERE, "screen_*.json"))):
        urls += [o["url"] for o in json.load(open(f, encoding="utf-8")).get("openings", []) if o.get("url")]
    urls = sorted(set(urls))
    with ThreadPoolExecutor(8) as ex:
        res = dict(zip(urls, ex.map(check, urls)))
    json.dump(res, open(os.path.join(HERE, "verify_links.json"), "w"), indent=1)
    bad = {u: v for u, v in res.items() if v["ok"] is not True}
    print(f"{len(urls)} urls, {len(urls) - len(bad)} ok, {len(bad)} not ok/unknown")
    for u, v in bad.items():
        print(" ", v["how"], u)


if __name__ == "__main__":
    main()
