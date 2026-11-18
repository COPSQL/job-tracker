# AI Usage Documentation

> Edit the sections marked **[EDIT]** so they describe what you actually did. Keep this honest:
> graders value accurate attribution more than a polished story.

## Tools Used
- Claude (Anthropic) to generate the first version of the project: schema, Flask routes, templates, CSS, README.
- **[EDIT]** Add any other tools (ChatGPT, Gemini, Copilot...) you used, and for what.

## Key Prompts
1. "Build the Job Application Tracker from this specification (MySQL, Flask, HTML/CSS)."
2. "Create a function to calculate skill match percentage and rank jobs." (became `calculate_match` in `app.py`)
3. **[EDIT]** Add the prompts you wrote yourself, e.g. debugging errors you hit while running it.

## What Worked Well
- Generating a config-driven CRUD layer: one `TABLES` dictionary in `app.py` describes each table, and shared routes and templates handle list, add, view, edit and delete for all four.
- Schema design: foreign keys with `ON DELETE CASCADE`, a CHECK constraint on salary, JSON columns, and sample data.
- The match algorithm: percent = matched skills / skills the job requires, case-insensitive, sorted by percent then matched count.
- **[EDIT]** Anything else that helped.

## What I Modified
- **[EDIT]** Describe your own changes: renamed variables, added fields, restyled the CSS, fixed bugs, changed validation, etc.
- **[EDIT]** Note anything you tested and found wrong in the AI output, and how you fixed it.

## Lessons Learned
- AI output must be run and tested; read every route to understand it before submitting.
- Giving the AI the full specification up front produced a consistent design.
- **[EDIT]** Add what you learned.
