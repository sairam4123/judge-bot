# JudgeBot

JudgeBot is a Discord courtroom roleplay bot. It lets server members open fictional cases, argue inside dedicated threads, attach evidence, and receive dramatic in-character rulings powered by Google Gemini.

The bot combines:

- Discord slash commands and interactive UI components
- SQLite-based persistence for courts, cases, participants, evidence, and logs
- AI-generated judge responses and case summaries
- A roleplay-first courtroom flow designed for community servers

---

## Table of Contents

- [Overview](#overview)
- [Feature Highlights](#feature-highlights)
- [How JudgeBot Works](#how-judgebot-works)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Running the Bot](#running-the-bot)
- [Commands and Interactions](#commands-and-interactions)
- [Data Storage](#data-storage)
- [AI Integration](#ai-integration)
- [Development Notes](#development-notes)
- [Troubleshooting](#troubleshooting)

---

## Overview

JudgeBot turns a Discord text channel into a fictional courtroom.

Once enabled in a server channel, members can:

1. File a case using a button and modal form.
2. Get a dedicated public thread for that case.
3. Present arguments back and forth in the thread.
4. Attach files as evidence.
5. Ask JudgeBot to summarize proceedings.
6. Let JudgeBot manage the scene with theatrical rulings, evidence requests, and verdict updates.

The current implementation loads a single court module on startup and stores runtime state in SQLite.

---

## Feature Highlights

### Court lifecycle

- `/start` activates JudgeBot in the current server channel.
- `/stop` deactivates the courtroom for that channel.
- Each activated channel is stored as a `court` record.

### Case filing

- Persistent **File a Case** button.
- Modal-based filing flow with:
  - case type
  - accusation reason
  - accused user selection
  - optional linked case threads
- Supported case types:
  - Civil
  - Criminal
  - Community
  - Counter-case
  - Other

### Per-case discussion threads

- Every case is created as its own public thread.
- The opening thread message shows:
  - accuser
  - accused users
  - reason
  - case type
  - status
  - current summary
  - verdict, when available

### Evidence workflow

- Evidence can be attached from:
  - the case action buttons
  - a context menu action
  - JudgeBot-requested evidence prompts
- Up to 2 files can be uploaded per evidence submission.
- Uploaded evidence is summarized with Gemini.
- Evidence is persisted and displayed through a gallery-style UI.

### AI judge behaviour

- JudgeBot responds in-character as a dramatic fictional judge.
- The bot reviews recent conversation logs, case details, and evidence summaries.
- Gemini can call internal tools to:
  - update a verdict
  - add a witness
  - close a case
  - request more evidence
  - search prior cases

### Summaries and search

- A context menu action can summarize case history.
- Running summaries are updated as conversation grows.
- Cases can be searched by keyword through a slash command.

### Case management

- Update case type, accused users, or reason.
- Close a case from the case thread.
- Closed threads are archived and locked.

---

## How JudgeBot Works

### 1. Enable the courtroom

Run `/start` in a server text channel. JudgeBot posts an announcement and adds a persistent **File a Case** button.

### 2. File a case

A user opens the filing modal, selects a case type, identifies the accused, and submits the accusation.

### 3. Create the case thread

JudgeBot creates a public thread for the case and stores its metadata in the database.

### 4. Run the hearing

Messages sent in the case thread are logged. JudgeBot reads the recent dialogue and responds as the judge.

### 5. Collect evidence

Participants can upload files. JudgeBot summarizes the uploads and includes that information in future case context.

### 6. Update the record

As the hearing continues, JudgeBot can refresh the case summary, update verdicts, and modify the top thread message.

### 7. Close the case

Cases can be closed manually or by the AI workflow. Closing a case updates the stored status and locks the thread.

---

## Architecture

JudgeBot is organized into a few core layers.

### Entry point

- `main.py` loads environment variables, creates the bot with full Discord intents, and starts the client.

### Bot container

- `judge_bot/bot.py` defines `JudgeBot`, initializes the SQLite database, loads the courts module, and syncs application commands on ready.

### Persistence layer

- `judge_bot/db.py` creates the SQLite connection and schema.
- `judge_bot/modules/courts/core/repositories.py` contains repository classes for cases, logs, evidences, courts, participants, and associated cases.

### Domain models

- `judge_bot/modules/courts/core/models.py` defines Pydantic models such as `Case`, `Court`, `LogEntry`, and `Evidence`.

### Court module

- `judge_bot/modules/courts/commands.py` provides slash commands, context menus, and the main message listener.
- `judge_bot/modules/courts/ui/` holds Discord modal and view implementations for filing, updating, closing, and evidencing cases.

### AI layer

- `judge_bot/genai/client.py` creates the Gemini client.
- `judge_bot/genai/generate.py` sends prompts to Gemini and processes tool calls.
- `judge_bot/modules/courts/tools.py` exposes tool functions the model can invoke.
- `judge_bot/modules/courts/core/prompt.py` contains the roleplay and case prompts.

---

## Project Structure

```text
judge-bot/
├── attachments/                     # Uploaded evidence saved locally before/while processing
├── db/                              # SQLite database directory used by the bot
├── exts/
│   └── cogs.py                      # Helper base cog and context menu registration
├── judge_bot/
│   ├── bot.py                       # Bot subclass and startup hook
│   ├── config.py                    # Minimal runtime config (default Gemini model)
│   ├── db.py                        # SQLite schema and connection manager
│   ├── utils.py                     # Shared helpers, summarization helpers, message builders
│   ├── genai/
│   │   ├── client.py                # Gemini client construction
│   │   └── generate.py              # Prompt execution and tool-call loop
│   └── modules/
│       └── courts/
│           ├── commands.py          # Slash commands, context menus, message listener
│           ├── tools.py             # AI-callable court tools
│           ├── core/
│           │   ├── models.py        # Pydantic models
│           │   ├── prompt.py        # Judge roleplay/system prompts
│           │   └── repositories.py  # Database repositories
│           └── ui/
│               ├── attach_evidence.py
│               ├── case_view.py
│               ├── close_case.py
│               ├── evidence_gallery.py
│               ├── file_case.py
│               ├── request_evidence_view.py
│               └── update_case.py
├── main.py                          # Process entry point
├── pyproject.toml                   # Project metadata and dependencies
├── uv.lock                          # Locked dependency versions
└── README.md
```

---

## Requirements

- Python 3.13 or newer
- A Discord bot application and token
- A Google AI API key for Gemini features
- A Discord build compatible with the UI components used by the project
- `uv` recommended for dependency management

### Python dependency notes

The project installs `discord.py` directly from Rapptz's GitHub repository rather than PyPI. That is important because the code uses newer Discord UI components such as file uploads and media gallery views.

Current declared dependencies:

- `discord-py` (Git source)
- `google-genai>=1.54.0`
- `pydantic>=2.12.5`
- `python-dotenv>=1.2.1`
- `strip-markdown>=1.3`

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/sairam4123/judge-bot.git
cd judge-bot
```

### 2. Install `uv` (recommended)

```bash
pip install uv
```

### 3. Create the environment and install dependencies

```bash
uv sync
```

If you prefer standard `venv` + `pip`, you can still install the project dependencies manually, but `uv sync` is the intended flow because it respects `pyproject.toml` and `uv.lock`.

### 4. Create required folders if missing

The bot expects these writable locations:

- `attachments/`
- `db/`

They already exist in the repository, but the runtime account must have write permission.

### 5. Configure your environment variables

Create a `.env` file in the project root.

---

## Environment Variables

Create `.env` with at least:

```env
DISCORD_TOKEN=your_discord_bot_token_here
GOOGLE_API_KEY=your_google_ai_api_key_here
```

### Variable reference

- `DISCORD_TOKEN`  
   Required. Used by `main.py` to log in to Discord.

- `GOOGLE_API_KEY`  
   Required for Gemini-backed summarization and judge response generation.

If `DISCORD_TOKEN` is missing, startup will fail immediately.

---

## Running the Bot

### With `uv`

```bash
uv run python main.py
```

### With an activated virtual environment

```bash
python main.py
```

On startup, JudgeBot will:

1. load `.env`
2. open or create the SQLite database
3. ensure required tables exist
4. load the courts extension
5. sync Discord application commands

---

## Commands and Interactions

## Slash commands

### `/start`

Activates JudgeBot in the current server channel.

Parameters:

- `name` - optional court name, defaults to `Default Court`
- `description` - optional court description

Effect:

- stores a court record
- posts the courtroom activation message
- shows the persistent **File a Case** button

### `/stop`

Deactivates JudgeBot in the current channel.

### `/list_cases`

Returns the currently stored cases.

### `/case_details`

Takes a case thread and returns a compact summary of the case record.

### `/search_cases`

Searches cases by keyword using the stored reason and summary fields.

## Context menu actions

### `Summarize`

Generates or refreshes a summary for the thread's case conversation.

### `Attach Evidence`

Opens the evidence upload modal for a case thread.

## Case thread buttons

Each case thread header message includes actions for:

- **Close Case**
- **Update Case**
- **Attach Evidence**

## Thread behaviour

When users post in an active case thread:

- the message is logged
- JudgeBot builds a prompt from:
  - case metadata
  - evidence summaries
  - recent dialogue
  - current verdict state
- Gemini generates the next judge response
- the response is posted back into the thread
- the case summary is updated periodically

---

## Data Storage

JudgeBot stores data in SQLite through `judge_bot/db.py`.

### Tables created automatically

- `cases`
- `associated_cases`
- `participants`
- `evidences`
- `log_entries`
- `courts`

### What gets stored

- **courts**: active courtroom channels by guild/channel
- **cases**: status, reason, type, verdict, summary, timestamps
- **participants**: accuser, accused, and witness relationships
- **evidences**: uploaded file metadata and AI summaries
- **log_entries**: conversation history for thread replay and summarization
- **associated_cases**: linked/counter-case references

### Database file location

The bot initializes SQLite with:

```text
db/judge_bot.db
```

Make sure the `db/` folder is writable.

### Evidence file handling

Uploaded files are temporarily or locally written under:

```text
attachments/
```

Those files are then uploaded to Google for summarization.

---

## AI Integration

JudgeBot uses Google Gemini for two main jobs:

1. **Conversation summarization**
2. **Roleplay judge responses**

### Default model

The default model is defined in `judge_bot/config.py`:

- `gemini-2.5-flash-lite`

### Prompt design

The prompts instruct the model to:

- remain in-character as a fictional judge
- avoid real legal advice
- guide the hearing theatrically
- request evidence when needed
- deliver structured verdicts
- use internal tools to update persistent case state

### Model tool calls

The AI layer can call internal functions that affect bot state:

- `update_verdict`
- `add_witness`
- `close_case`
- `request_evidence`
- `search_case`
- `reopen_case`

This allows the model to do more than chat; it can also update the courtroom record.

---

## Development Notes

### Important implementation details

- The bot is created with `discord.Intents.all()`.
- Commands are synced in `on_ready()`.
- The current module loading path is hard-coded to `judge_bot.modules.courts.commands`.
- Repositories are thin wrappers over raw SQLite statements.
- Pydantic models provide typed structures for repository output.

### Current limitations

- No automated test suite is currently included.
- Startup configuration is minimal and mostly environment-driven.
- Database access is synchronous SQLite.
- The bot assumes a single persistent process managing the database file.

---

## Troubleshooting

### Bot does not start

Check that:

- `.env` exists
- `DISCORD_TOKEN` is present
- dependencies installed correctly
- your Python version is 3.13+

### Gemini features fail

Check that:

- `GOOGLE_API_KEY` is valid
- the account has access to the configured Gemini model
- outbound network access is available

### Slash commands do not appear

Check that:

- the bot was invited with the `applications.commands` scope
- the bot has connected successfully
- command sync finished on startup

### JudgeBot does not respond in threads

Check that:

- the thread belongs to a stored case
- the case is not closed
- the bot has permission to read, send messages, and create thread posts
- privileged intents are enabled for the Discord application if required by your bot setup

### Evidence uploads fail

Check that:

- the `attachments/` folder is writable
- the bot has permission to access attachments
- Gemini file processing is available and not rate-limited

---

## Summary

JudgeBot is a Discord courtroom roleplay system with:

- interactive case filing
- threaded hearings
- SQLite persistence
- evidence management
- AI-powered judge responses and summaries

It is a good foundation for a community roleplay court, moderation-themed server gimmick, or experiment in AI-assisted Discord interactions.
