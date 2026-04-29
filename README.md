# Job Application Tracker

A lightweight, **fully local** desktop CRM for managing your job hunt — written in Python with a Tkinter GUI. No accounts, no cloud, no telemetry. Your data lives in a single `applications.json` file next to the app.

![platform](https://img.shields.io/badge/platform-Windows-blue) ![python](https://img.shields.io/badge/python-3.8%2B-green) ![license](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Features

- **Full application tracker** with company, role, location, status, source, contact, dates, priority, links, and notes.
- **🌐 Auto-fill from URL** — paste a LinkedIn / Indeed / Greenhouse / Lever job URL and the app extracts company, role, location, and description automatically.
- **💰 Compensation tracking** — record budget available, your ask, and whether it's negotiable.
- **📅 Built-in date & time pickers** — no typing `YYYY-MM-DD` if you don't want to.
- **🔔 Reminders** — get a popup at launch when a follow-up is due.
- **🔎 Live search** — top-right box filters by company / role / location as you type.
- **↕ Sortable columns** — click any header to sort A→Z; click again for Z→A.
- **🎯 Smart views** — `All` / `Action Needed` / `In Progress` / `Applied This Week`.
- **📋 Board view** — Kanban-style cards grouped by status.
- **⟳ One-click update** — pull the latest version from GitHub from inside the app.
- **❓ In-app help** — this README, rendered inside the app.

---

## Quick Install (Windows)

Open PowerShell and run:

```powershell
iwr -useb https://raw.githubusercontent.com/Sharmagowtham709/JobTracker/main/install.ps1 | iex
```

The installer will:

1. Install **Git** (via winget) if missing.
2. Install **uv** (Python version manager) if missing.
3. Use uv to install a private **Python 3.12** (does not affect any system Python).
4. Clone the repo to `%USERPROFILE%\JobTracker`.
5. Generate the application icon.
6. Create a **"Job Tracker"** shortcut on your Desktop.

When it finishes, double-click the desktop shortcut. Done.

### Custom install location

```powershell
iwr -useb https://raw.githubusercontent.com/Sharmagowtham709/JobTracker/main/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File install.ps1 -InstallDir "D:\Tools\JobTracker"
```

### Manual install

```powershell
git clone https://github.com/Sharmagowtham709/JobTracker.git
cd JobTracker
uv python install 3.12
uv run --python 3.12 python make_icon.py
powershell -ExecutionPolicy Bypass -File create_shortcut.ps1
```

---

## Running the App

**Easiest:** double-click the `Job Tracker` shortcut on your Desktop.

**From the terminal:**

```powershell
cd $env:USERPROFILE\JobTracker
uv run --python 3.12 python tracker.py
```

**Silently (no console window):** double-click `launch.vbs` in the install folder.

---

## Using the App

### Adding a job

1. Click **➕ Add**.
2. (Optional) Paste the job URL into the top field and click **🌐 Fetch** — Company, Role, Location, Source, and Notes will auto-fill.
3. Fill in the manual section (Date Applied, Status, Priority, etc.). New entries auto-suggest:
   - **Date Applied** = today
   - **Next Action Date** = today + 6 days
   - **Reminder** = today + 6 days at 10:00
4. Click **💾 Save**.

### Editing / deleting

- **Double-click** any row to edit.
- Select a row and click **✏ Edit** or **🗑 Delete**.

### Searching

The **🔎 search box** in the top-right filters live by company, role, or location. Press `Esc` in the box to clear.

### Sorting

Click any column header to sort. The active column shows ▲ (ascending) or ▼ (descending). Click again to flip direction.

### Views

Use the **View** dropdown:

| View | Shows |
|---|---|
| **All** | every entry |
| **Action Needed** | rows where `Next Action Date` ≤ today, sorted by priority |
| **In Progress** | excludes `Offer` and `Rejected` |
| **Applied This Week** | rows applied within the last 7 days |

### Board view

Click **📋 Board View** for a Kanban-style window with cards grouped by status.

### Reminders

When you launch the app, it checks for reminders whose date+time has passed. A popup lists due reminders, and they're auto-dismissed so you don't see them again.

---

## Updating

Click the **⟳ Update** button in the bottom-right of the main window. The app:

1. Runs `git fetch` to check the remote.
2. Tells you how many commits behind you are.
3. On confirmation, runs `git pull --ff-only` and asks you to restart the app.

Your `applications.json` is untouched by updates (it's gitignored).

To update by re-running the installer instead:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

---

## Data & Privacy

- **All data stays local.** The app never connects to the internet except:
  - When you click **🌐 Fetch** (it fetches the job URL you paste).
  - When you click **⟳ Update** (it talks to GitHub via git).
- Your data file: `applications.json` in the install directory.
- **Back up by copying that one file.**

---

## Field Reference

| Field | Type | Notes |
|---|---|---|
| Company | text | **Required.** |
| Role | text | Job title. |
| Location | text | City / remote / hybrid. |
| Date Applied | date | YYYY-MM-DD; picker available. |
| Status | select | 📤 Applied · 🔍 Under Review · 📅 Interview Scheduled · 🎉 Offer · ❌ Rejected · 🔇 No Response |
| Source | select | LinkedIn · Company Website · Referral · Job Portal · Other |
| Contact | text | Recruiter name, email, etc. |
| Last Follow-up | date | When you last reached out. |
| Next Action Date | date | Drives the **Action Needed** view. |
| Reminder Date / Time | date + HH:MM | Triggers a popup at next launch when due. |
| Priority | select | High · Medium · Low |
| Budget Available | text | What the company is offering. |
| My Ask | text | What you're targeting. |
| Negotiable? | select | Yes · No · Unknown |
| Job Link | URL | Click **🔗 Open Link** to launch in browser. |
| Notes | text | Free-form. |

---

## Troubleshooting

**"Python was not found" when launching**
The installer uses uv-managed Python, not system Python. Always launch via the desktop shortcut or `uv run --python 3.12 python tracker.py`.

**Update button says "not a git checkout"**
You installed by downloading a zip instead of cloning. Re-install via `install.ps1` (or `git clone …`) to enable updates.

**🌐 Fetch returns nothing for LinkedIn**
LinkedIn sometimes serves a sign-in wall to bots. The app sends a browser-like User-Agent and tries multiple parsers, but some pages still return no data. Fill the form manually in that case.

**Reminders aren't firing**
Reminders only check **at launch**. Close and reopen the app to re-check. Once a reminder fires, it's marked dismissed and won't fire again.

**"Tip: New entries auto-suggest…" is in the way**
That's the bottom status bar — collapse the window taller; or ignore it, it's purely informational.

---

## Repo Layout

```
JobTracker/
├── tracker.py              # main application
├── make_icon.py            # generates tracker.ico
├── launch.vbs              # silent launcher (no console)
├── create_shortcut.ps1     # creates Desktop shortcut
├── install.ps1             # one-shot Windows installer
├── tracker.ico             # app icon (generated)
├── applications.json       # YOUR DATA (gitignored)
└── README.md
```

---

## Contributing

PRs welcome. Style: stdlib-only (no extra dependencies), Python 3.8+ compatible, ttk widgets preferred over raw tk.

---

## License

MIT
