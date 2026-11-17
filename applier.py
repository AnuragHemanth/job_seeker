"""Opens a job page, tries to apply, and finds an HR email if one is shown."""
import re

from config import FULL_NAME, PHONE, RESUME_PATH, SITE_LOGINS

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
IGNORED_EMAIL_PARTS = ("noreply", "no-reply", "donotreply", "example.", "sentry", "wixpress")


# Exact login fields and button for each site (checked on the live login pages)
LOGIN_FORMS = {
    "naukri": {
        "url": "https://www.naukri.com/nlogin/login",
        "email": "#usernameField", "password": "#passwordField",
        "submit": "button[type=submit]:has-text('Login')",
    },
    "internshala": {
        "url": "https://internshala.com/login",
        "email": "#email", "password": "#password", "submit": "#login_submit",
    },
}


def login_if_needed(page, site: str, login_url: str = "") -> bool:
    """Logs in to the site. Returns True if the login page was left (login likely worked)."""
    email, password = SITE_LOGINS.get(site, ("", ""))
    form = LOGIN_FORMS.get(site)
    if not email or not password or not form:
        return False
    page.goto(form["url"], wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    page.locator(form["email"]).first.fill(email)
    page.locator(form["password"]).first.fill(password)
    page.locator(form["submit"]).first.click()
    page.wait_for_timeout(6000)
    ok = "login" not in page.url.lower()
    log_line = f"[{site}] login {'OK' if ok else 'NOT confirmed'} (url: {page.url[:80]})"
    print(log_line)
    return ok


def find_hr_email(page) -> str:
    text = page.inner_text("body")
    for match in EMAIL_RE.findall(text):
        low = match.lower()
        if not any(bad in low for bad in IGNORED_EMAIL_PARTS):
            return match
    return ""


def _fill_common_fields(page) -> None:
    """Fill name/email/phone inputs on a form if they are visible and empty."""
    from resume_reader import load_profile
    contact = {}
    try:
        contact = load_profile(RESUME_PATH)["contact"]
    except Exception:
        pass
    mapping = [
        ("input[name*=name i], input[id*=name i], input[placeholder*=name i]", FULL_NAME),
        ("input[type=email], input[name*=email i], input[id*=email i]", contact.get("email", "")),
        ("input[type=tel], input[name*=phone i], input[name*=mobile i], input[id*=phone i]", PHONE),
    ]
    for selector, value in mapping:
        if not value:
            continue
        boxes = page.locator(selector)
        for i in range(boxes.count()):
            box = boxes.nth(i)
            try:
                if box.is_visible() and not box.input_value():
                    box.fill(value)
            except Exception:
                pass


def _close_popups(page) -> None:
    """Dismiss pop-ups (job alert / subscription) that cover the Apply button."""
    page.keyboard.press("Escape")
    for selector in [".subscription_alert .close", ".modal.show .close", ".modal.show button[data-dismiss=modal]"]:
        close = page.locator(selector)
        for i in range(close.count()):
            try:
                if close.nth(i).is_visible():
                    close.nth(i).click(timeout=2000)
            except Exception:
                pass
    page.wait_for_timeout(500)


def try_apply(page, job_url: str) -> tuple[str, str]:
    """Returns (status, note). status is 'applied', 'external', 'no-button' or 'error'."""
    page.goto(job_url, wait_until="load", timeout=60000)
    page.wait_for_timeout(2000)
    hr_email = find_hr_email(page)

    apply_pattern = re.compile(r"^\s*apply", re.I)
    target = None
    for _ in range(3):  # Apply buttons often render late; retry a few times
        buttons = page.get_by_role("button", name=apply_pattern)
        links = page.get_by_role("link", name=apply_pattern)
        target = buttons.first if buttons.count() else (links.first if links.count() else None)
        if target is not None:
            break
        page.wait_for_timeout(3000)
    if target is None:
        return "no-button", hr_email

    _close_popups(page)
    try:
        with page.expect_popup(timeout=5000) as popup_info:
            target.evaluate("el => el.click()")
        new_page = popup_info.value
        new_page.wait_for_load_state("domcontentloaded")
        page = new_page
    except Exception:
        try:
            target.evaluate("el => el.click()")
        except Exception as e:
            return f"error: {str(e)[:150]}", hr_email
    page.wait_for_timeout(3000)

    # Upload resume if the form asks for it
    file_inputs = page.locator("input[type=file]")
    if file_inputs.count() and RESUME_PATH.exists():
        try:
            file_inputs.first.set_input_files(str(RESUME_PATH))
            page.wait_for_timeout(2000)
        except Exception:
            pass

    _fill_common_fields(page)

    submit = page.get_by_role(
        "button", name=re.compile(r"submit|send application|apply now|continue", re.I)
    )
    if submit.count():
        try:
            submit.first.click()
            page.wait_for_timeout(3000)
            return "applied", hr_email
        except Exception as e:
            return f"error: {e}", hr_email

    # The site sent us to an outside company page we can't fill automatically
    return "external", hr_email
