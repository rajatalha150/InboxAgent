# InboxAgent

**InboxAgent** is a privacy-first, locally hosted desktop application designed to automatically organize your email inbox. Using custom pattern-matching rules and powerful local AI classification, InboxAgent manages and sorts your incoming emails without ever sending your data or credentials to cloud services.

![InboxAgent Dashboard](https://github.com/rajatalha150/InboxAgent/assets/dashboard_preview.png)

## Key Features
- **Advanced Rule Engine:** Create rules based on sender, recipient, subject, body keywords, and email age.
- **Dynamic Polling:** Choose between Fixed, Dynamic (business hours), and Aggressive polling modes to control how often the agent checks your mail.
- **Batch Processing:** Configure the maximum number of emails to process in a single cycle to manage performance on large inboxes.
- **Local AI Classification:** Hook directly into [Ollama](https://ollama.com) to categorize emails using natural language prompts (e.g. *"Is this an invoice?"*).
- **Powerful Action Engine:** Move, flag, label, mark as read, delete, or dynamically auto-sort emails into folders.
- **Universal Provider Support:** Connects securely to Google Workspace, Microsoft Outlook, Yahoo, Fastmail, or any generic IMAP service.
- **Premium Dark Theme UI:** Manage rules, view logs, and track statistics in a sleek, customizable desktop dashboard.
- **Privacy by Design:** Everything runs securely on your own machine. Zero cloud telemetry.

### Future Features
- **Cycle Summaries (NLG):** Implement a basic Natural Language Generation (NLG) system to create more human-like, paragraph-style summaries of each processing cycle.

## Installation

### Pre-built Package
You can install the fully bundled `.deb` package on Debian/Ubuntu systems:
```bash
sudo dpkg -i inbox-agent_0.1.0_all.deb
```
*(All backend services, PyQt6 dependencies, and binaries are fully self-contained on installation).*

### Run from Source
```bash
pip install .              # Install CLI backend only
pip install ".[gui]"       # Install Desktop Application
```

### Windows Compilation
If you wish to compile the application and bundle the setup `.exe` installer directly on Windows, please refer to the [Windows Build Guide](WINDOWS_BUILD_GUIDE.md).

## Getting Started
To get started, simply configure your email credentials (such as your Gmail App Password) and begin writing your first automated routing rules.

Launch the application desktop environment by running:
```bash
inbox-agent --gui
```

For comprehensive instructions on writing matching templates, constructing AI Prompts, establishing system-level autostart workflows, and advanced headless configuration, please see the [Complete User Guide](GUIDE.md).

## License

**Copyright (c) 2026 Peak Services Inc.**  
All Rights Reserved.

This application is strictly bound by a Proprietary and Confidential Software License. It is not open-source. For terms regarding use, modification, distribution, and liability, please review the strict terms set forth in the [LICENSE](LICENSE) file enclosed in this repository.
