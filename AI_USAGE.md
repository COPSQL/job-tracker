# AI Usage Documentation

## Tools Used
- Claude (Anthropic) to generate the first version of the project: schema, Flask routes, templates, CSS, README.
- Claude also gave step-by-step help installing MySQL and Python on my Mac and fixing setup errors.
- No other AI tools were used.

## Key Prompts
1. "Build the Job Application Tracker from this specification (MySQL, Flask, HTML/CSS)."
2. "Create a function to calculate skill match percentage and rank jobs." (became `calculate_match` in `app.py`)
3. "Give me step-by-step instructions for a Mac, I have never used these tools."
4. I pasted my Terminal errors (MySQL server not running, expired MySQL password, git needing developer tools) and asked how to fix each one.

## What Worked Well
- Generating a config-driven CRUD layer: one `TABLES` dictionary in `app.py` describes each table, and shared routes and templates handle list, add, view, edit and delete for all four.
- Schema design: foreign keys with `ON DELETE CASCADE`, a CHECK constraint on salary, JSON columns, and sample data.
- The match algorithm: percent = matched skills / skills the job requires, case-insensitive, sorted by percent then matched count.
- Explaining error messages and giving the exact commands to fix them.

## What I Modified
- Set my own MySQL password and connection settings (DB_PASSWORD) so the app connects on my computer.
- Reset my MySQL root password after it expired, loaded schema.sql, and set up my own GitHub repository and git settings.
- Tested add, edit and delete on the pages myself, and added a .gitignore so Python cache files are not committed.

## Lessons Learned
- AI output must be run and tested; I read through each route to understand it before submitting.
- Giving the AI the full specification up front produced a consistent design.
- Most problems were setup problems, not code problems; pasting the exact error into the AI got a fix quickly.