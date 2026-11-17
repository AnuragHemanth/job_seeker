"""Weekly job-application runner.

Run manually:   python main.py
Run by schedule: see setup_schedule.ps1
"""
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path

import config
from config import (
    APPLICATIONS_CSV, DATA_DIR, HEADLESS, JOB_TITLE, LOG_DIR, MAX_APPLICATIONS_PER_RUN,
    RESUME_PATH, RUN_LOG, SEEN_FILE, SEND_HR_EMAILS, SITE_LOGINS,
)
from resume_reader import load_profile

LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(RUN_LOG, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("job-bot")

CSV_FIELDS = ["time", "site", "title", "url", "apply_status", "hr_email", "hr_email_sent", "note"]


def load_seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return set(SEEN_FILE.read_text(encoding="utf-8").splitlines())


def mark_seen(url: str) -> None:
    with SEEN_FILE.open("a", encoding="utf-8") as f:
        f.write(url + "\n")


def write_row(row: dict) -> None:
    new_file = not APPLICATIONS_CSV.exists()
    with APPLICATIONS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    from playwright.sync_api import sync_playwright
    from applier import login_if_needed, try_apply
    from hr_mailer import send_hr_email
    from job_sites import SITES, collect_jobs

    log.info("=== Run started %s | role=%s | resume=%s", datetime.now(), JOB_TITLE, RESUME_PATH)
    if not RESUME_PATH.exists():
        log.error("Resume not found at %s. Add it and try again.", RESUME_PATH)
        return
    profile = load_profile(RESUME_PATH)
    log.info("Skills read from resume: %s", ", ".join(profile["skills"]) or "none found")

    seen = load_seen()
    applied_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=HEADLESS) if _has_chrome(p) \
            else p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()

        for site in SITES:
            if config.ENABLED_SITES and site not in config.ENABLED_SITES:
                continue
            if applied_count >= MAX_APPLICATIONS_PER_RUN:
                break
            try:
                login_url = {
                    "naukri": "https://www.naukri.com/nlogin/login",
                    "internshala": "https://internshala.com/login",
                    "wellfound": "https://wellfound.com/login",
                    "indeed": "https://secure.indeed.com/auth",
                }[site]
                if any(SITE_LOGINS.get(site, ("", ""))):
                    login_if_needed(page, site, login_url)

                jobs = collect_jobs(page, site)
                log.info("[%s] found %d job links", site, len(jobs))
            except Exception as e:
                log.error("[%s] search failed: %s", site, e)
                continue

            for job in jobs:
                if applied_count >= MAX_APPLICATIONS_PER_RUN:
                    break
                if job["url"] in seen:
                    continue
                row = {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "site": site, "title": job["title"], "url": job["url"],
                    "apply_status": "", "hr_email": "", "hr_email_sent": "no", "note": "",
                }
                if config.DRY_RUN:
                    row["apply_status"] = "dry-run (not applied)"
                    write_row(row)
                    log.info("[%s] DRY RUN found: %s | %s", site, job["title"][:60], job["url"])
                    continue
                try:
                    status, hr_email = try_apply(page, job["url"])
                    row["apply_status"] = status
                    row["hr_email"] = hr_email
                    if status == "applied":
                        applied_count += 1
                    if hr_email and SEND_HR_EMAILS:
                        send_hr_email(hr_email, job.get("company", ""), job["title"])
                        row["hr_email_sent"] = "yes"
                    # only finished jobs are remembered; failed ones are retried next run
                    if status in ("applied", "external", "no-button"):
                        mark_seen(job["url"])
                except Exception as e:
                    row["apply_status"] = "error"
                    row["note"] = str(e)[:200]
                    log.warning("Failed on %s: %s", job["url"], e)
                write_row(row)
                log.info("[%s] %s -> %s", site, job["title"][:60], row["apply_status"])

        browser.close()

    log.info("=== Run finished. Applied: %d", applied_count)


def _has_chrome(p) -> bool:
    """Use the Chrome already installed on this PC if Playwright can find it."""
    try:
        browser = p.chromium.launch(channel="chrome", headless=True)
        browser.close()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
