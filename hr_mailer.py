"""Sends an application email with the resume attached to the HR address found on the job page."""
import smtplib
from email.message import EmailMessage

from config import FULL_NAME, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, JOB_TITLE, RESUME_PATH


def send_hr_email(to_address: str, company: str, job_title: str) -> None:
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        raise RuntimeError("GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing in .env")

    msg = EmailMessage()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = to_address
    msg["Subject"] = f"Application for {job_title or JOB_TITLE} position"
    body = (
        f"Dear Hiring Team{f' at {company}' if company else ''},\n\n"
        f"I am writing to apply for the {job_title or JOB_TITLE} position. "
        f"My resume is attached for your review.\n\n"
        f"I would welcome the opportunity to discuss how my experience can contribute "
        f"to your team.\n\n"
        f"Thank you for your time.\n\n"
        f"Best regards,\n{FULL_NAME}"
    )
    msg.set_content(body)

    if RESUME_PATH.exists():
        data = RESUME_PATH.read_bytes()
        subtype = "pdf" if RESUME_PATH.suffix.lower() == ".pdf" else "vnd.openxmlformats-officedocument.wordprocessingml.document"
        msg.add_attachment(data, maintype="application", subtype=subtype, filename=RESUME_PATH.name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
