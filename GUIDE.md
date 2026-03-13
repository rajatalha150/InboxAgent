# InboxAgent — User Guide

**Version:** 0.1.0
**Copyright (c) 2026 Peak Services Inc.** — [peakservices-inc.com](https://peakservices-inc.com)
**License:** Proprietary (See LICENSE)

---

## Table of Contents

1. [What Is InboxAgent?](#what-is-inboxagent)
2. [Key Features](#key-features)
3. [Installation](#installation)
4. [Getting Started](#getting-started)
5. [Configuration](#configuration)
   - [Setting Up Email Accounts](#setting-up-email-accounts)
   - [Writing Rules](#writing-rules)
   - [AI Classification](#ai-classification)
6. [Available Actions](#available-actions)
7. [Using the Desktop GUI](#using-the-desktop-gui)
8. [Using the Command Line](#using-the-command-line)
9. [The Dashboard](#the-dashboard)
10. [How It Works Internally](#how-it-works-internally)
11. [Troubleshooting](#troubleshooting)
12. [Building & Packaging](#building--packaging)
13. [Project Structure](#project-structure)

---

## What Is InboxAgent?

InboxAgent is a privacy-first desktop application that automatically organizes your email. You define simple rules (or use optional local AI), and InboxAgent watches your inbox and takes action — moving, labeling, flagging, or deleting messages — all without sending your data to any external cloud service.

Everything runs on your own machine. Your email credentials and message content never leave your computer.

---

## Key Features

- **Automatic email organization** — rules run continuously in the background.
- **Multiple email accounts** — connect Gmail, Outlook, Yahoo, or any IMAP provider.
- **Pattern matching** — filter by sender, recipient, subject keywords, or body text.
- **Local AI classification** — ask natural-language questions about emails using Ollama (optional).
- **Rich set of actions** — move to folders, flag, delete, mark read/unread, add Gmail labels, or auto-sort by sender.
- **Premium Dark Theme Desktop GUI** — a sleek graphical interface with a dashboard, live activity feed, account management, rule editor, session logs, built-in tooltips (`?`), and settings.
- **Cycle Summaries** — detailed text-based log summaries of polling sessions with process stats.
- **Command-line mode** — run headless on a server or in the background.
- **System tray integration** — minimizes to your system tray and runs quietly.
- **Dry-run mode** — test your rules without making any changes.
- **Privacy by design** — no cloud, no telemetry, no third-party servers.

---

## Installation

### From .deb package (Debian/Ubuntu)

```bash
sudo dpkg -i inbox-agent_0.1.0_all.deb
```

This installs everything you need. No internet connection is required at install time — all dependencies are bundled.

### From source (pip)

```bash
pip install .              # CLI only
pip install ".[gui]"       # CLI + desktop GUI
```

### Requirements

- Python 3.10 or newer
- An IMAP-capable email account (Gmail, Outlook, Yahoo, Fastmail, etc.)
- For Gmail: an App Password (not your regular password)
- For AI features: Ollama installed and running locally (optional)

---

## Getting Started

### Step 1 — Configure your email account

Edit `config/accounts.yaml`:

```yaml
accounts:
  - name: my-gmail
    imap_server: imap.gmail.com
    email: you@gmail.com
    password: "your-app-password"
```

For Gmail, you must use an **App Password**. Go to your Google Account > Security > 2-Step Verification > App Passwords, and generate one.

### Step 2 — Write your first rule

Edit `config/rules.yaml`:

```yaml
rules:
  - name: newsletters-to-folder
    match:
      subject: ["newsletter", "digest", "weekly update"]
    action:
      move_to: "Newsletters"
```

This moves any email with "newsletter", "digest", or "weekly update" in the subject line into a folder called "Newsletters".

### Step 3 — Launch

**Desktop GUI:**
```bash
inbox-agent --gui
```

**Command line:**
```bash
inbox-agent
```

Click **Start Agent** in the GUI (or just run the CLI command) and InboxAgent begins polling your inbox.

---

## Configuration

All configuration lives in YAML files inside the `config/` directory (or wherever you point `--config-dir`).

### Setting Up Email Accounts

File: `config/accounts.yaml`

```yaml
accounts:
  - name: personal-gmail
    imap_server: imap.gmail.com
    imap_port: 993
    email: alice@gmail.com
    password: "xxxx-xxxx-xxxx-xxxx"
    ssl: true

  - name: work-outlook
    imap_server: outlook.office365.com
    email: alice@company.com
    password: "your-password"
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | — | A friendly name for the account (used in logs and the dashboard) |
| `imap_server` | Yes | — | IMAP server address |
| `imap_port` | No | 993 | IMAP port number |
| `email` | Yes | — | Your email address |
| `password` | Yes | — | Your password or app password |
| `ssl` | No | true | Use SSL/TLS encryption |

You can add as many accounts as you like. InboxAgent processes them all in each polling cycle.

### Writing Rules

File: `config/rules.yaml`

Rules have two parts: **match conditions** (what to look for) and **actions** (what to do).

```yaml
rules:
  - name: flag-from-boss
    match:
      from: "boss@company.com"
    action:
      flag: true
      mark_read: false

  - name: delete-spam-domains
    match:
      from:
        - "*@spammer.com"
        - "*@junkmail.net"
    action:
      delete: true

  - name: sort-receipts
    match:
      subject: ["receipt", "order confirmation", "invoice"]
      from: "*@*.com"
    action:
      move_to: "Receipts"
      mark_read: true
```

#### Match Conditions

All conditions in a rule must match (AND logic). If you list multiple values for a condition, any one of them matching is enough (OR within the condition).

| Condition | Type | How it matches |
|-----------|------|----------------|
| `from` | string or list | Glob pattern match on sender address. `*@domain.com` matches any sender at that domain. Case-insensitive. |
| `to` | string or list | Glob pattern match on recipient address. Same syntax as `from`. |
| `subject` | string or list | Substring match on the subject line. Case-insensitive. Matches if any keyword is found. |
| `body` | string or list | Substring match on the email body text. Case-insensitive. Matches if any keyword is found. |
| `ai_prompt` | string | A yes/no question sent to the local AI model (see AI Classification below). |

#### Examples

Match emails from anyone at example.com with "urgent" in the subject:
```yaml
match:
  from: "*@example.com"
  subject: ["urgent"]
```

Match emails from multiple senders:
```yaml
match:
  from:
    - "alice@example.com"
    - "bob@example.com"
    - "*@alerts.example.com"
```

### AI Classification

InboxAgent can use a local AI model (via Ollama) to classify emails using natural language. This is entirely optional — if Ollama is not installed, AI rules are simply skipped.

#### Setup

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model: `ollama pull llama3.2:3b`
3. Ollama runs as a background service automatically

#### Using AI in rules

Add an `ai_prompt` field to your rule's match conditions. The prompt must be a yes/no question:

```yaml
rules:
  - name: job-opportunities
    match:
      ai_prompt: "Is this email about a job opportunity or interview invitation?"
    action:
      move_to: "Jobs"
      flag: true

  - name: meeting-requests
    match:
      ai_prompt: "Is this email requesting or scheduling a meeting?"
    action:
      label: "Meetings"
```

The AI reads each email's sender, subject, and body (first 2000 characters), then answers your question with "yes" or "no". If the answer is "yes", the condition matches.

You can combine AI prompts with regular pattern matching:

```yaml
- name: important-client-requests
  match:
    from: "*@bigclient.com"
    ai_prompt: "Does this email contain an urgent request or action item?"
  action:
    flag: true
    move_to: "Priority"
```

#### Choosing a model

Pass `--model` when launching InboxAgent to use a different model:

```bash
inbox-agent --gui --model mistral:7b
```

Smaller models (3B parameters) are faster. Larger models are more accurate. The default `llama3.2:3b` is a good balance for email classification.

---

## Available Actions

When a rule matches an email, one or more actions are executed:

| Action | Value | What it does |
|--------|-------|-------------|
| `move_to` | folder name | Moves the email to the specified folder. Creates the folder if it doesn't exist. |
| `flag` | `true` / `false` | Flags (`true`) or unflags (`false`) the email. Flagged emails show a star/flag in most email clients. |
| `delete` | `true` | Deletes the email. **This stops all other actions for this email.** |
| `mark_read` | `true` | Marks the email as read (sets the Seen flag). |
| `mark_unread` | `true` | Marks the email as unread (removes the Seen flag). |
| `label` | label name | Adds a Gmail label. Only works with Gmail accounts. |
| `auto_sort_by_sender` | `true` or config dict | Dynamically sorts emails. Can be configured via GUI to extract: Full Sender Email, Sender Domain Only, Sender Name, Full Subject Line, or First Word of Subject. Automatically sanitizes strings to create safe IMAP target folders. |

You can combine multiple actions in a single rule:

```yaml
action:
  move_to: "Archive/Newsletters"
  mark_read: true
  flag: false
```

---

## Using the Desktop GUI

Launch the GUI with:

```bash
inbox-agent --gui
```

Or start minimized to the system tray:

```bash
inbox-agent --minimized
```

The GUI has five tabs:

### Dashboard
The main control center. Shows the agent's current status (Stopped, Starting, Running, Error), live statistics (accounts connected, emails processed, rules triggered, errors, cycles completed), and a real-time activity feed. Start and stop the agent from here.

### Activity
A dedicated tab to view, refresh, and clear dynamically generated cycle summaries from the agent's background executions. Select a summary to view in-depth details about uptime, emails scanned, and rule occurrences.

### Accounts
View and manage your configured email accounts.

### Rules
View and manage your email processing rules.

### Logs
A live scrolling log of everything the agent is doing — useful for debugging.

### Settings
Configure the poll interval, AI model, dry-run mode, and other options. Changes made while the agent is running require a restart to take effect (a banner will notify you).

### System Tray

When you close the window, InboxAgent minimizes to the system tray instead of quitting. Right-click the tray icon for options:

- **Start Agent** / **Stop Agent** — control the agent without opening the window
- **Open** — bring the window back
- **Quit** — fully exit the application

Double-click the tray icon to reopen the window.

---

## Using the Command Line

For headless or server use, run InboxAgent without `--gui`:

```bash
inbox-agent --config-dir /etc/inbox-agent --interval 120 --log-level INFO
```

### All command-line options

| Option | Default | Description |
|--------|---------|-------------|
| `--config-dir PATH` | `config/` | Path to the directory containing `accounts.yaml` and `rules.yaml` |
| `--interval SECONDS` | `60` | How often to check for new emails (in seconds) |
| `--dry-run` | off | Log what actions would be taken without actually doing anything |
| `--model MODEL` | `llama3.2:3b` | Ollama model to use for AI classification |
| `--uid-file PATH` | `processed_uids.json` | File to track which emails have already been processed |
| `--log-level LEVEL` | `INFO` | Logging detail: `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `--gui` | off | Launch the desktop GUI |
| `--minimized` | off | Start the GUI minimized to the system tray |

### Running as a system service (Linux)

InboxAgent ships with a systemd service file. After installing the .deb package:

```bash
sudo systemctl enable inbox-agent
sudo systemctl start inbox-agent
```

The service runs as a dedicated `inbox-agent` user and reads configuration from `/etc/inbox-agent/`.

---

## The Dashboard

The dashboard's Recent Activity panel provides a live, categorized view of everything the agent is doing:

| Icon | Category | Meaning |
|------|----------|---------|
| Blue dot | Connection | Successfully connected to an email account |
| Gray dot | Processing | Currently processing an email |
| Green dot | Rule | A rule was triggered and its actions executed |
| Red dot | Error | Something went wrong (expandable for details) |

Each entry includes a timestamp (HH:MM:SS).

**Filtering:** Use the dropdown to show only one category (Connections, Processing, Rules, or Errors), or type in the search box to filter by text.

**Error details:** Error entries can be expanded to show technical details. Double-click an error row to open a popup with the full error text (copyable for bug reports).

**Clear:** The Clear button wipes all activity entries.

---

## How It Works Internally

Here is what happens when InboxAgent runs:

1. **Load configuration** — InboxAgent reads `accounts.yaml` and `rules.yaml` from the config directory.

2. **Connect to accounts** — It opens an IMAP connection (with SSL) to each configured email account.

3. **Poll loop** — Every N seconds (configurable), it checks each account's INBOX for new emails:

   a. **Fetch new UIDs** — gets the list of email UIDs (unique IDs) in the inbox.

   b. **Skip already-processed** — compares against a local JSON file that tracks which UIDs have been handled.

   c. **Parse each new email** — downloads the raw email and extracts the sender, recipient, subject, and body text.

   d. **Evaluate rules** — checks each rule's conditions against the parsed email. All conditions in a rule must match (AND logic). Rules are checked in order.

   e. **Execute actions** — for each matching rule, the configured actions are executed (move, flag, delete, etc.).

   f. **Record as processed** — the email UID is saved so it won't be processed again.

4. **Poll Cycles** — After scanning all accounts, a "Cycle" is completed. The agent enters a sleep interval (e.g., 60s) counting in 1-second ticks. This prevents rate-limiting and allows instant interrupts if "Stop Agent" is clicked.

5. **Graceful shutdown** — on stop (or Ctrl+C in CLI mode), InboxAgent finishes its current operation, disconnects from all email servers, and exits cleanly.

### Privacy guarantees

- All processing happens locally on your machine.
- Email content is never sent to external servers.
- AI classification uses Ollama, which runs 100% locally.
- No analytics, telemetry, or tracking of any kind.
- Your credentials are stored only in your local config files.

### Architecture overview

```
┌─────────────────────────────────────────────────────────┐
│                     InboxAgent                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  config/accounts.yaml ──> Config Loader                 │
│  config/rules.yaml    ──> Config Loader                 │
│                              │                          │
│                              v                          │
│                        Agent Core                       │
│                     (poll loop, state)                   │
│                              │                          │
│              ┌───────────────┼───────────────┐          │
│              v               v               v          │
│        IMAP Client    Rule Engine     AI Classifier     │
│       (per account)   (conditions)    (Ollama, local)   │
│              │               │               │          │
│              v               v               v          │
│         Email Parser  ──> Match? ──> Actions Engine     │
│                          (move, flag, delete, label)    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  GUI (PyQt6)           │  CLI (terminal)                │
│  - Dashboard           │  - Blocking loop               │
│  - Accounts tab        │  - Signal handling              │
│  - Rules tab           │  - Logging to stdout            │
│  - Activity tab        │                                │
│  - Logs tab            │                                │
│  - Settings tab        │                                │
│  - System tray         │                                │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "No accounts connected successfully"
- Check that your IMAP server address and port are correct.
- If using 2FA, **you must use an App Password, not your regular password**. 
  - [How to create a Gmail App Password](https://support.google.com/accounts/answer/185833)
  - [How to create an Outlook App Password](https://support.microsoft.com/en-us/account-billing/manage-app-passwords-for-two-step-verification-d6dc8c6d-4bf7-4851-ad95-6d07799387e9)
  - [How to create a Yahoo App Password](https://help.yahoo.com/kb/generate-and-manage-third-party-app-passwords-sln15241.html)
- Make sure "IMAP access" is enabled in your email provider's settings.
- Check your firewall — port 993 (IMAP over SSL) must be open.

### Rules are not matching
- Use `--dry-run` mode to see what the agent is doing without taking action.
- Set `--log-level DEBUG` for detailed matching information.
- Remember that all conditions in a rule must match (AND logic).
- Pattern matching is case-insensitive, but check for typos in email addresses.

### AI classification is not working
- Make sure Ollama is installed and running: `ollama list` should show your models.
- Pull a model if needed: `ollama pull llama3.2:3b`
- AI rules are silently skipped if Ollama is unavailable — check the logs at DEBUG level.

### Emails are being processed again after restart
- Make sure the `--uid-file` points to a persistent location.
- The default `processed_uids.json` is in the current working directory — if you run from different directories, use an absolute path.

### GUI won't start
- Install GUI dependencies: `pip install inbox-agent[gui]` (requires PyQt6).
- On Linux, you may need system Qt libraries: `sudo apt install libqt6-dev`.

---

## Building & Packaging

### Build a .deb package (Debian/Ubuntu)

```bash
cd packaging
bash build_deb.sh
```

This creates a fully self-contained `.deb` file with all Python dependencies bundled. No internet is needed at install time.

### Build a Windows installer (.msi)

```bash
python packaging/build_msi.py bdist_msi
```

### Build a standalone executable (PyInstaller)

```bash
cd packaging
pyinstaller open-email.spec
```

---

## Project Structure

```
src/open_email/
├── main.py              # Entry point (CLI + GUI launcher)
├── agent_core.py        # Core polling loop, state machine, callbacks
├── config_loader.py     # YAML config file loading and validation
├── imap_client.py       # IMAP connection, folder ops, email fetching
├── email_parser.py      # RFC822 email parsing into structured objects
├── rule_engine.py       # Rule evaluation (pattern + AI matching)
├── ai_classifier.py     # Ollama integration for AI classification
├── actions.py           # Action execution (move, flag, delete, etc.)
├── platform/
│   └── autostart.py     # OS-specific autostart registration
└── gui/
    ├── app.py           # Main window, system tray, tab container
    ├── agent_thread.py  # QThread wrapper for agent core
    ├── tabs/
    │   ├── dashboard.py # Status, stats, activity feed
    │   ├── activity.py  # Cycle summaries layout
    │   ├── accounts.py  # Account management
    │   ├── rules.py     # Rule management
    │   ├── logs.py      # Live log viewer
    │   └── settings.py  # Application settings
    └── widgets/
        └── log_handler.py  # Custom Qt log handler
```

---

**InboxAgent** is developed and maintained by **Peak Services Inc.**
Website: [peakservices-inc.com](https://peakservices-inc.com)
