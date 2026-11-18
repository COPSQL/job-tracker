"""Job Application Tracker - Flask application."""
import json
import re
from datetime import date

import mysql.connector
from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)

import database as db

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Each table is described once; generic CRUD routes below use this config.
# "sql" is the SELECT used for lists and detail pages (main table aliased as t).
TABLES = {
    "companies": {
        "pk": "company_id", "singular": "Company", "plural": "Companies",
        "sql": "SELECT t.* FROM companies t",
        "order": "t.company_name",
        "cascade": "Its jobs, applications and contacts will also be deleted.",
        "columns": [("company_name", "Company"), ("industry", "Industry"),
                    ("city", "City"), ("state", "State"), ("website", "Website")],
        "fields": [
            {"name": "company_name", "label": "Company name", "type": "text", "required": True, "max": 100},
            {"name": "industry", "label": "Industry", "type": "text", "max": 50},
            {"name": "website", "label": "Website", "type": "url", "max": 200},
            {"name": "city", "label": "City", "type": "text", "max": 50},
            {"name": "state", "label": "State", "type": "text", "max": 50},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
    "jobs": {
        "pk": "job_id", "singular": "Job", "plural": "Jobs",
        "sql": ("SELECT t.*, c.company_name FROM jobs t "
                "JOIN companies c ON c.company_id = t.company_id"),
        "order": "t.date_posted DESC, t.job_id DESC",
        "cascade": "Its applications will also be deleted.",
        "columns": [("job_title", "Job title"), ("company_name", "Company"),
                    ("job_type", "Type"), ("salary", "Salary"),
                    ("date_posted", "Posted"), ("requirements", "Requirements")],
        "fields": [
            {"name": "company_id", "label": "Company", "type": "fk", "required": True,
             "display": "company_name",
             "fk_sql": "SELECT company_id, company_name FROM companies ORDER BY company_name"},
            {"name": "job_title", "label": "Job title", "type": "text", "required": True, "max": 100},
            {"name": "job_type", "label": "Job type", "type": "select", "options": JOB_TYPES},
            {"name": "salary_min", "label": "Minimum salary ($)", "type": "number"},
            {"name": "salary_max", "label": "Maximum salary ($)", "type": "number"},
            {"name": "job_url", "label": "Job posting URL", "type": "url", "max": 300},
            {"name": "date_posted", "label": "Date posted", "type": "date"},
            {"name": "requirements", "label": "Required skills", "type": "skills",
             "help": "Separate skills with commas, e.g. Python, SQL, Flask"},
        ],
    },
    "applications": {
        "pk": "application_id", "singular": "Application", "plural": "Applications",
        "sql": ("SELECT t.*, j.job_title, c.company_name FROM applications t "
                "JOIN jobs j ON j.job_id = t.job_id "
                "JOIN companies c ON c.company_id = j.company_id"),
        "order": "t.application_date DESC, t.application_id DESC",
        "cascade": "",
        "columns": [("job_title", "Job"), ("company_name", "Company"),
                    ("application_date", "Applied on"), ("status", "Status"),
                    ("resume_version", "Resume"), ("cover_letter_sent", "Cover letter")],
        "fields": [
            {"name": "job_id", "label": "Job", "type": "fk", "required": True,
             "display": "job_title",
             "fk_sql": ("SELECT j.job_id, CONCAT(j.job_title, ' at ', c.company_name) "
                        "FROM jobs j JOIN companies c ON c.company_id = j.company_id "
                        "ORDER BY c.company_name, j.job_title")},
            {"name": "application_date", "label": "Application date", "type": "date", "required": True},
            {"name": "status", "label": "Status", "type": "select", "options": STATUSES},
            {"name": "resume_version", "label": "Resume version", "type": "text", "max": 50},
            {"name": "cover_letter_sent", "label": "Cover letter sent", "type": "checkbox"},
            {"name": "interview_data", "label": "Interview data (JSON)", "type": "json",
             "help": 'Optional. Example: {"rounds": [{"type": "Phone", "date": "2026-02-01"}]}'},
        ],
    },
    "contacts": {
        "pk": "contact_id", "singular": "Contact", "plural": "Contacts",
        "sql": ("SELECT t.*, c.company_name FROM contacts t "
                "JOIN companies c ON c.company_id = t.company_id"),
        "order": "t.contact_name",
        "cascade": "",
        "columns": [("contact_name", "Name"), ("title", "Title"), ("company_name", "Company"),
                    ("email", "Email"), ("phone", "Phone")],
        "fields": [
            {"name": "company_id", "label": "Company", "type": "fk", "required": True,
             "display": "company_name",
             "fk_sql": "SELECT company_id, company_name FROM companies ORDER BY company_name"},
            {"name": "contact_name", "label": "Contact name", "type": "text", "required": True, "max": 100},
            {"name": "title", "label": "Title", "type": "text", "max": 100},
            {"name": "email", "label": "Email", "type": "email", "max": 100},
            {"name": "phone", "label": "Phone", "type": "text", "max": 20},
            {"name": "linkedin_url", "label": "LinkedIn URL", "type": "url", "max": 200},
            {"name": "notes", "label": "Notes", "type": "textarea"},
        ],
    },
}

TABLE_ROUTE = "<any(%s):table>" % ",".join(TABLES)


# ---------------------------------------------------------------- helpers
def parse_skills(raw):
    """'Python, sql ,Python' -> ['Python', 'sql'] (trimmed, de-duplicated)."""
    seen, skills = set(), []
    for item in raw.split(","):
        item = item.strip()
        if item and item.lower() not in seen:
            seen.add(item.lower())
            skills.append(item)
    return skills


def field_options(field):
    """(value, label) pairs for select / foreign-key fields."""
    if field["type"] == "select":
        return [(o, o) for o in field["options"]]
    if field["type"] == "fk":
        return [tuple(row.values()) for row in db.query(field["fk_sql"])]
    return []


def convert(field, raw):
    """Validate one non-empty string and convert it for storage. Raises ValueError."""
    kind, label = field["type"], field["label"]
    if kind in ("text", "email", "url") and len(raw) > field["max"]:
        raise ValueError(f"{label} must be at most {field['max']} characters.")
    if kind == "email" and not EMAIL_RE.match(raw):
        raise ValueError("Enter a valid email address.")
    if kind == "url" and not re.match(r"^https?://\S+$", raw):
        raise ValueError("Enter a full URL starting with http:// or https://.")
    if kind == "number":
        if not raw.isdigit():
            raise ValueError(f"{label} must be a whole number of zero or more.")
        return int(raw)
    if kind == "date":
        try:
            return date.fromisoformat(raw).isoformat()
        except ValueError:
            raise ValueError("Enter a valid date.")
    if kind == "select":
        if raw not in field["options"]:
            raise ValueError(f"Choose a valid {label.lower()}.")
    if kind == "fk":
        valid = {str(v) for v, _ in field_options(field)}
        if raw not in valid:
            raise ValueError(f"Choose a valid {label.lower()}.")
        return int(raw)
    if kind == "skills":
        return json.dumps(parse_skills(raw))
    if kind == "json":
        try:
            return json.dumps(json.loads(raw))
        except json.JSONDecodeError as err:
            raise ValueError(f"Not valid JSON: {err.msg}.")
    return raw


def parse_form(cfg, form):
    """Return (values for the database, {field: error message})."""
    values, errors = {}, {}
    for field in cfg["fields"]:
        name = field["name"]
        if field["type"] == "checkbox":
            values[name] = 1 if form.get(name) else 0
            continue
        raw = (form.get(name) or "").strip()
        values[name] = None
        if not raw:
            if field.get("required"):
                errors[name] = f"{field['label']} is required."
            continue
        try:
            values[name] = convert(field, raw)
        except ValueError as err:
            errors[name] = str(err)
    low, high = values.get("salary_min"), values.get("salary_max")
    if low is not None and high is not None and low > high:
        errors["salary_max"] = "Maximum salary must be at least the minimum."
    return values, errors


def load_json(value):
    """MySQL JSON columns come back as text; turn them into Python objects."""
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


def prepare_row(cfg, row):
    """Decode JSON columns and add display-only fields."""
    for field in cfg["fields"]:
        if field["type"] in ("skills", "json"):
            row[field["name"]] = load_json(row[field["name"]])
    if "salary_min" in row:
        low, high = row["salary_min"], row["salary_max"]
        if low is not None and high is not None:
            row["salary"] = f"${low:,} - ${high:,}"
        elif low is not None or high is not None:
            row["salary"] = f"${(low if low is not None else high):,}"
        else:
            row["salary"] = None
    return row


def form_values(cfg, row):
    """Turn a stored row into strings an edit form can show."""
    values = {}
    for field in cfg["fields"]:
        value = row[field["name"]]
        if value is None:
            values[field["name"]] = ""
        elif field["type"] == "skills":
            values[field["name"]] = ", ".join(value)
        elif field["type"] == "json":
            values[field["name"]] = json.dumps(value, indent=2)
        else:
            values[field["name"]] = value
    return values


def get_record(cfg, record_id):
    row = db.query(f"{cfg['sql']} WHERE t.{cfg['pk']} = %s", (record_id,), one=True)
    if row is None:
        abort(404)
    return prepare_row(cfg, row)


def calculate_match(user_skills, jobs):
    """Rank jobs by the share of their required skills the user has."""
    have = {s.lower() for s in user_skills}
    results = []
    for job in jobs:
        required = job["requirements"] or []
        if not required:
            continue
        matched = [s for s in required if s.lower() in have]
        if not matched:
            continue
        results.append({
            "job_id": job["job_id"],
            "job_title": job["job_title"],
            "company_name": job["company_name"],
            "percent": round(100 * len(matched) / len(required)),
            "matched": matched,
            "missing": [s for s in required if s.lower() not in have],
            "total": len(required),
        })
    results.sort(key=lambda r: (-r["percent"], -len(r["matched"]), r["job_title"]))
    return results


# ----------------------------------------------------------------- routes
@app.route("/")
def dashboard():
    counts = db.query(
        "SELECT (SELECT COUNT(*) FROM companies) AS companies, "
        "(SELECT COUNT(*) FROM jobs) AS jobs, "
        "(SELECT COUNT(*) FROM applications) AS applications, "
        "(SELECT COUNT(*) FROM contacts) AS contacts", one=True)
    status_rows = db.query("SELECT status, COUNT(*) AS n FROM applications GROUP BY status")
    by_status = {s: 0 for s in STATUSES}
    by_status.update({r["status"]: r["n"] for r in status_rows})
    recent = db.query(
        f"{TABLES['applications']['sql']} ORDER BY t.application_date DESC, "
        "t.application_id DESC LIMIT 5")
    return render_template("dashboard.html", counts=counts, by_status=by_status,
                           recent=recent, cfg=TABLES["applications"])


@app.route("/job-match")
def job_match():
    raw = request.args.get("skills", "").strip()
    skills = parse_skills(raw)
    results, searched = [], bool(skills)
    if searched:
        cfg = TABLES["jobs"]
        jobs = [prepare_row(cfg, r) for r in db.query(cfg["sql"])]
        results = calculate_match(skills, jobs)
    return render_template("job_match.html", raw=raw, skills=skills,
                           results=results, searched=searched)


@app.route(f"/{TABLE_ROUTE}/")
def list_records(table):
    cfg = TABLES[table]
    rows = [prepare_row(cfg, r) for r in db.query(f"{cfg['sql']} ORDER BY {cfg['order']}")]
    return render_template(f"{table}.html", cfg=cfg, table=table, rows=rows)


@app.route(f"/{TABLE_ROUTE}/<int:record_id>")
def detail(table, record_id):
    cfg = TABLES[table]
    return render_template("detail.html", cfg=cfg, table=table,
                           row=get_record(cfg, record_id), record_id=record_id)


def save_form(table, record_id=None):
    """Shared handler for the add and edit forms."""
    cfg = TABLES[table]
    existing = get_record(cfg, record_id) if record_id else None
    options = {f["name"]: field_options(f) for f in cfg["fields"] if f["type"] in ("select", "fk")}
    if request.method == "POST":
        values, errors = parse_form(cfg, request.form)
        if not errors:
            names = [f["name"] for f in cfg["fields"]]
            args = [values[n] for n in names]
            if record_id:
                assignments = ", ".join(f"{n} = %s" for n in names)
                db.execute(f"UPDATE {table} SET {assignments} WHERE {cfg['pk']} = %s",
                           args + [record_id])
                flash(f"{cfg['singular']} updated.", "ok")
            else:
                marks = ", ".join(["%s"] * len(names))
                db.execute(f"INSERT INTO {table} ({', '.join(names)}) VALUES ({marks})", args)
                flash(f"{cfg['singular']} added.", "ok")
            return redirect(url_for("list_records", table=table))
        shown = {f["name"]: request.form.get(f["name"], "") for f in cfg["fields"]}
        shown.update({f["name"]: bool(request.form.get(f["name"]))
                      for f in cfg["fields"] if f["type"] == "checkbox"})
    else:
        errors = {}
        if existing:
            shown = form_values(cfg, existing)
        else:
            shown = {f["name"]: "" for f in cfg["fields"]}
            if table == "applications":
                shown.update({"application_date": date.today().isoformat(), "status": "Applied"})
            elif table == "jobs":
                shown["job_type"] = "Full-time"
    return render_template("form.html", cfg=cfg, table=table, values=shown, errors=errors,
                           options=options, editing=bool(record_id), record_id=record_id)


@app.route(f"/{TABLE_ROUTE}/new", methods=["GET", "POST"])
def new_record(table):
    return save_form(table)


@app.route(f"/{TABLE_ROUTE}/<int:record_id>/edit", methods=["GET", "POST"])
def edit_record(table, record_id):
    return save_form(table, record_id)


@app.route(f"/{TABLE_ROUTE}/<int:record_id>/delete", methods=["POST"])
def delete_record(table, record_id):
    cfg = TABLES[table]
    get_record(cfg, record_id)  # 404 if it does not exist
    db.execute(f"DELETE FROM {table} WHERE {cfg['pk']} = %s", (record_id,))
    flash(f"{cfg['singular']} deleted.", "ok")
    return redirect(url_for("list_records", table=table))


@app.errorhandler(mysql.connector.Error)
def database_error(err):
    return render_template("error.html", message=str(err)), 500


@app.errorhandler(404)
def not_found(_err):
    return render_template("error.html", message="That page or record does not exist."), 404


if __name__ == "__main__":
    app.run(debug=True)
