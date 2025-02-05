# -*- coding: utf-8 -*-
import os
import csv
import smtplib
import logging
import pandas as pd
import traceback
from jobspy import scrape_jobs
from email.message import EmailMessage

# ✅ Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", force=True)

# ✅ Load Email Credentials from Environment Variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

if not all([SENDER_EMAIL, APP_PASSWORD, RECIPIENT_EMAIL]):
    logging.error("❌ Missing email credentials. Set them in GitHub Secrets.")
    exit(1)

# ✅ Job Roles
job_roles = [
    "Business Analyst", "BI Analyst", "Data Business Analyst", "Business Data Analyst",
    "Business Systems Analyst", "IT Business Analyst", "Technical Business Analyst",
    "Reporting Analyst", "Strategy Analyst", "Decision Analyst", "Insights Analyst",
    "Financial Business Analyst", "Product Analyst", "Process Analyst", "Operations Analyst",
    "Business Operations Analyst", "Agile Business Analyst", "Digital Business Analyst",
    "Systems Analyst", "Associate Business Analyst", "Graduate Business Analyst"
]

# ✅ Experience Filters
experience_filters = ["0-3 years", "Entry Level", "Junior", "Freshers", "1+ years", "2+ years", "Associate"]

# ✅ Exclusion Keywords
senior_exclusion_keywords = ["Senior", "Staff", "Lead", "Principal", "Director", "Sr.", "Head", "Expert"]
non_cs_exclusion_keywords = [
    "Civil Engineer", "Mechanical", "Electrical Engineer", "Doctor", "Nurse",
    "Pharmacist", "HR", "Marketing", "Sales", "Finance", "Accounting",
    "Construction", "Architect", "Legal", "Therapist", "Dentist",
    "Physical Therapy", "Retail", "Fashion", "Customer Service",
    "Professor", "Biology", "Chemistry", "Physics", "Biotech"
]
exclusion_keywords = ["US citizen", "US citizenship", "Green card", "security clearance"]

# ✅ Master DataFrame
all_jobs_df = pd.DataFrame()

def fetch_jobs(search_term, location="USA", results_wanted=50, hours_old=24):
    """Fetch job listings, filter relevant jobs, and return as DataFrame."""
    try:
        logging.info(f"🔍 Searching for jobs: {search_term}...")
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "zip_recruiter", "google"],
            search_term=search_term,
            google_search_term=f"{search_term} software jobs in {location} since yesterday",
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed="USA",
        )

        if jobs.empty:
            logging.warning(f"⚠️ No jobs found for {search_term}.")
            return pd.DataFrame()

        # ✅ Apply filtering
        filtered_jobs = jobs[
            ~jobs["description"].str.contains("|".join(exclusion_keywords), case=False, na=False) &
            jobs["title"].str.contains("|".join(job_roles), case=False, na=False) &
            (jobs["title"].str.contains("|".join(experience_filters), case=False, na=False) |
             jobs["description"].str.contains("|".join(experience_filters), case=False, na=False)) &
            ~jobs["title"].str.contains("|".join(senior_exclusion_keywords), case=False, na=False) &
            ~jobs["title"].str.contains("|".join(non_cs_exclusion_keywords), case=False, na=False)
        ].copy()

        if filtered_jobs.empty:
            logging.warning(f"⚠️ No suitable jobs found for {search_term} after filtering.")
            return pd.DataFrame()

        filtered_jobs["search_term"] = search_term
        return filtered_jobs

    except Exception as e:
        logging.error(f"❌ Error fetching jobs for {search_term}: {e}")
        logging.error(traceback.format_exc())
        return pd.DataFrame()

# ✅ Fetch and filter jobs
for role in job_roles:
    jobs_df = fetch_jobs(role)
    if not jobs_df.empty:
        all_jobs_df = pd.concat([all_jobs_df, jobs_df], ignore_index=True)

# ✅ Save jobs to CSV
final_csv_filename = "JobGenieMagic.csv"
if not all_jobs_df.empty:
    all_jobs_df.drop_duplicates(subset=["job_url" if "job_url" in all_jobs_df.columns else "title"], keep="first", inplace=True)
    all_jobs_df.to_csv(final_csv_filename, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
    logging.info(f"✅ Jobs saved in {final_csv_filename}")
else:
    logging.warning("⚠️ No jobs found to save.")

# ✅ Email Function
def send_email_with_attachment(file):
    if not os.path.exists(file):
        logging.error(f"❌ No file found: {file}")
        return

    msg = EmailMessage()
    msg["Subject"] = "🔥 JobGenie 🧞‍♂️ - Fresh 0-3 Year Tech Roles! - DailyPaper"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    # Email Body
    email_body = """\
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #4CAF50;">Hello Future Tech Superstar! 🌟</h2>

            <p>I hope this email finds you <strong>smiling, motivated, and ready to take on the world</strong>! 💪✨</p>

            <p>Here’s your daily list of <strong>fresh job listings</strong> that match your skills and experience (0-3 years):</p>

            <ul>
                <li>📂 <strong>Handpicked jobs from top platforms</strong></li>
                <li>🔍 <strong>No 'US Citizenship Required' filters</strong></li>
                <li>🚀 <strong>Your gateway to an exciting tech career!</strong></li>
            </ul>

            <p>Take a deep breath, grab your favorite coffee ☕, and check out these listings! The right job is out there waiting for someone <strong>exactly like you</strong>—smart, ambitious, and full of potential.</p>

            <h3 style="color: #ff5722;">You got this! 🎯🌟</h3>

            <p><em>Wishing you success,</em></p>
            <p><strong>JobGenie Bot 🧞‍♂️🤖</strong></p>
        </body>
    </html>
    """
    msg.add_alternative(email_body, subtype="html")

    with open(file, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="csv", filename=file)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        logging.info("✅ Email sent successfully!")
    except Exception as e:
        logging.error(f"❌ Email failed: {e}")
        logging.error(traceback.format_exc())

# ✅ Send email
send_email_with_attachment(final_csv_filename)