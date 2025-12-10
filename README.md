# judge-bot

A Discord roleplay courtroom bot that lets users file cases, attach evidence, and get dramatic JudgeBot rulings.

## Features

- `/start` to activate the courtroom in a server (adds the "File a Case" button); `/stop` to deactivate.
- "File a Case" modal with case type (Civil, Criminal, Community, Counter-case, Other), accused users, reason, and optional associated case threads for counter-cases.
- Each case gets its own thread with persistent storage in `cases.json` and `courts.json`, plus buttons to update or close a case.
- Context menu commands: **Summarize** (uses Google Gemini to summarize recent logs) and **Attach Evidence** (upload up to two files, auto-summarize, and post a gallery).
- Slash commands: `/list_cases` to list active cases and `/case_details` to view a specific case.
- JudgeBot roleplay responses, logging conversations, and keeping running summaries.

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

Ensure the process can write to `cases.json`, `courts.json`, and an `attachments/` directory for uploaded evidence.

## Requirements

- Python 3.14 (recommended) — 3.8+ supported
- UV (for package management)
- discord.py
- google-genai

## License

See LICENSE file for details.
