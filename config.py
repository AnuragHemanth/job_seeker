"""Loads settings from .env. All secrets live in .env only."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "y")


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


FULL_NAME = os.getenv("FULL_NAME", "").strip()
PHONE = os.getenv("PHONE", "").strip()
RESUME_PATH = Path(os.getenv("RESUME_PATH", str(BASE_DIR / "resume.pdf")))

JOB_TITLE = os.getenv("JOB_TITLE", "Full Stack Developer").strip()
LOCATION = os.getenv("LOCATION", "Remote").strip()
MAX_APPLICATIONS_PER_RUN = _int("MAX_APPLICATIONS_PER_RUN", 20)

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
SEND_HR_EMAILS = _bool("SEND_HR_EMAILS", True)

HEADLESS = _bool("HEADLESS", False)

# true = only search and log matching jobs; never submits applications or emails
DRY_RUN = _bool("DRY_RUN", False)

# comma-separated list of sites to use, e.g. "naukri,internshala"; blank = all sites
ENABLED_SITES = [s.strip() for s in os.getenv("ENABLED_SITES", "").split(",") if s.strip()]

# site name -> (email, password) read from .env
SITE_LOGINS = {
    "naukri": (os.getenv("NAUKRI_EMAIL", ""), os.getenv("NAUKRI_PASSWORD", "")),
    "internshala": (os.getenv("INTERNSHALA_EMAIL", ""), os.getenv("INTERNSHALA_PASSWORD", "")),
    "wellfound": (os.getenv("WELLFOUND_EMAIL", ""), os.getenv("WELLFOUND_PASSWORD", "")),
    "indeed": (os.getenv("INDEED_EMAIL", ""), os.getenv("INDEED_PASSWORD", "")),
}

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
SEEN_FILE = DATA_DIR / "seen_urls.txt"
APPLICATIONS_CSV = LOG_DIR / "applications.csv"
RUN_LOG = LOG_DIR / "run.log"
