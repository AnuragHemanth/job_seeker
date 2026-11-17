# Weekly Job Applier (local)

Reads your resume, searches Indeed, Naukri, Internshala and Wellfound for your job title,
tries to apply, and emails HR (resume attached) when an HR address is on the job page.
Everything runs on your PC. Nothing is sent to any service except the job sites and Gmail.

## One-time setup

1. Install Python packages:
   ```
   cd c:\Users\HP\Desktop\automation
   pip install -r requirements.txt
   python -m playwright install chromium
   ```
2. Put your resume in this folder as `resume.pdf` (or `resume.docx`).
3. Copy `.env.example` to `.env` and fill it in:
   - `FULL_NAME`, `PHONE`, `RESUME_PATH`
   - `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` (create the App Password at
     https://myaccount.google.com/apppasswords; needs 2-Step Verification on)
   - Logins for the sites where you have accounts
4. Check your resume is read correctly:
   ```
   python resume_reader.py
   ```

## Running

- Test run (watch the browser): `python main.py`
- Weekly schedule: right-click PowerShell, run as normal user:
  `powershell -ExecutionPolicy Bypass -File setup_schedule.ps1`

## Where to see results

- `logs/applications.csv` — every job: site, title, link, apply status, HR email, whether the email was sent
- `logs/run.log` — what happened each run
- `data/seen_urls.txt` — jobs already processed (so the same job is never applied to twice)

## Important limits

- Job sites change their pages often. Some sites will return 0 jobs or fail to apply until
  the selectors in `job_sites.py` and `applier.py` are updated. Check `run.log` after the first runs.
- Jobs that send you to a company's own website are marked `external`. The bot does not
  fill those forms; you need to apply on them yourself.
- HR emails are sent only when an HR/contact email is printed on the job page. The bot does
  not search for HR people on LinkedIn.
- Check the job sites' terms. Automated applications can break their rules and may lead to account restrictions.
- Keep `MAX_APPLICATIONS_PER_RUN` modest (10–20) so applications stay relevant.
- Keep `.env` private. It is listed in `.gitignore`.
