"""Job search for each site. Returns a list of {site, title, company, url}.

NOTE: Job sites change their HTML often. The URL patterns below are the
best known as of 2026; if a site returns 0 jobs, update its entry in SITES.
"""
import re
from urllib.parse import quote_plus

from config import JOB_TITLE, LOCATION

# site -> search URL template, and regex a job-detail link must match
SITES = {
    "indeed": {
        "search": "https://www.indeed.com/jobs?q={q}&l={l}",
        "link_pattern": r"/(viewjob|rc/clk|pagead/clk)\?",
        "base": "https://www.indeed.com",
    },
    "naukri": {
        "search": "https://www.naukri.com/{slug}-jobs",
        "link_pattern": r"naukri\.com/job-listings-",
        "base": "https://www.naukri.com",
    },
    "internshala": {
        "search": "https://internshala.com/jobs/{slug}-jobs",
        "link_pattern": r"/job/detail/",
        "base": "https://internshala.com",
    },
    "wellfound": {
        "search": "https://wellfound.com/role/l/{slug}/{loc}",
        "link_pattern": r"/jobs/\d+|/company/[^/]+/jobs/",
        "base": "https://wellfound.com",
    },
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def search_url(site: str) -> str:
    cfg = SITES[site]
    return cfg["search"].format(
        q=quote_plus(JOB_TITLE),
        l=quote_plus(LOCATION),
        slug=_slug(JOB_TITLE),
        loc=_slug(LOCATION) or "remote",
    )


def collect_jobs(page, site: str, limit: int = 30) -> list[dict]:
    """Open the search page and pull out job links."""
    cfg = SITES[site]
    page.goto(search_url(site), wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    jobs, seen = [], set()
    anchors = page.locator("a[href]")
    for i in range(min(anchors.count(), 400)):
        a = anchors.nth(i)
        href = a.get_attribute("href") or ""
        if not re.search(cfg["link_pattern"], href):
            continue
        url = href if href.startswith("http") else cfg["base"] + href
        url = url.split("#")[0]
        if url in seen:
            continue
        seen.add(url)
        title = (a.inner_text() or "").strip().split("\n")[0][:120]
        jobs.append({"site": site, "title": title or JOB_TITLE, "company": "", "url": url})
        if len(jobs) >= limit:
            break
    return jobs
