# Job Application Tracker

A Flask + MySQL web app for tracking job applications, with CRUD for companies, jobs,
applications and contacts, a statistics dashboard, and a Job Match page that ranks jobs by
how many of their required skills you have.

## Requirements
- Python 3.9+
- MySQL 8.0+ (JSON columns and CHECK constraints are used)

## Setup
1. Clone the repository and open the folder.
2. (Optional) create a virtual environment: `python -m venv venv` then activate it.
3. Install dependencies: `pip install -r requirements.txt`
4. Create the database and sample data (this drops and recreates `job_tracker`):
   `mysql -u root -p < schema.sql`
5. Set your MySQL credentials (defaults: host `localhost`, user `root`, empty password):
   - macOS/Linux: `export DB_PASSWORD='your_password'`
   - Windows PowerShell: `$env:DB_PASSWORD = 'your_password'`
   - Optional: `DB_HOST`, `DB_USER`, `DB_NAME`
6. Run: `python app.py`
7. Open http://127.0.0.1:5000

## Features
- **Database:** 4 tables with foreign keys (deleting a company or job also deletes its children), JSON columns `jobs.requirements` and `applications.interview_data`.
- **CRUD:** add, list, view, edit and delete (with a confirmation prompt) for every table, with server-side validation (required fields, dates, URLs, emails, salary range, valid JSON).
- **Dashboard:** record counts, applications by status, latest applications.
- **Job Match:** enter skills, e.g. `Python, SQL, Flask`; jobs are ranked by match % with the missing skills listed.

## Project structure
```
app.py          Flask routes, validation, job match algorithm
database.py     MySQL connection helpers
schema.sql      Database creation script + sample data
templates/      Jinja HTML templates
static/         style.css
AI_USAGE.md     GenAI usage documentation
```

## Demo video
See `demo.mp4` (add your 3-7 minute recording to the repository root).
