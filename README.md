# judge-bot

A Discord roleplay courtroom bot that lets users file cases, attach evidence, and get dramatic JudgeBot rulings.

## Features

- `/start` and `/stop` to activate/deactivate the courtroom in a server (adds/removes the "File a Case" button)
- "File a Case" modal: choose case type (Civil, Criminal, Community, Counter-case, Other), accused users, reason, and optionally link associated case threads
- Each case gets its own thread with persistent storage in `cases.json` and `courts.json`, with buttons to update or close a case
- Context menu: **Summarize** (uses Google Gemini for log summaries), **Attach Evidence** (upload up to two files, auto-summarize, and post a gallery)
- Slash commands: `/list_cases` (list active cases), `/case_details` (view a specific case)
- JudgeBot roleplay responses, conversation logging, and running summaries

## Project Structure

```
judge-bot/
├── cases.json
├── courts.json
├── data_access.py
├── db.py
├── JudgeBot_DB.session.sql
├── main.py
├── pyproject.toml
├── README.md
├── db/
├── exts/
│   ├── cogs.py
│   └── __pycache__/
├── judge_bot/
│   ├── __init__.py
│   ├── bot.py
│   ├── db.py
│   ├── utils.py
│   ├── genai/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── generate.py
│   └── modules/
│       └── courts/
│           ├── commands.py
│           ├── tools.py
│           ├── core/
│           │   ├── __init__.py
│           │   ├── models.py
│           │   ├── prompt.py
│           │   └── repositories.py
│           └── ui/
│               ├── __init__.py
│               ├── attach_evidence.py
│               ├── case_view.py
│               ├── close_case.py
│               ├── evidence_gallery.py
│               ├── file_case.py
│               ├── request_evidence_view.py
│               └── update_case.py
```

## Installation (with UV)

1. Clone the repository
2. Install UV if you haven't already:
   ```bash
   pip install uv
   ```
3. Install dependencies:
   ```bash
   uv sync
   ```

## Running the Project

Run the bot:

```bash
python main.py
```

If you prefer using UV directly:

```bash
uv run python main.py
```

## Configuration

Create a `.env` file in the project root with:

- `DISCORD_TOKEN` — your Discord bot token
- `GOOGLE_API_KEY` — used for Gemini-based summaries

Ensure the process can write to `cases.json`, `courts.json`, and the `attachments/` directory for uploaded evidence.

## Requirements

- Python 3.14 (recommended) — 3.8+ supported
- UV (for package management)
- discord.py
- google-genai

## License

See LICENSE file for details.
