# Help — Job Application Tracker

Welcome! This is the in-app help. It covers everything you need to know to use the tracker day-to-day.

> Looking for installation or update instructions? Open the GitHub repo from the **Open repo on GitHub** button at the bottom.

---

## Adding a Job Application

1. Click **➕ Add** on the toolbar.
2. *(Optional but recommended)* Paste the job posting URL into the field at the top of the dialog and click **🌐 Fetch**. The app will try to extract:
   - Company
   - Role
   - Location
   - Source
   - A short description in Notes
3. Fill in the manual section (status, priority, your ask, etc.). New entries auto-suggest:
   - **Date Applied** = today
   - **Next Action Date** = today + 6 days
   - **Reminder** = today + 6 days at 10:00
4. Click **💾 Save**.

> **Tip:** the URL fetch works best on Greenhouse, Lever, and other ATS sites. LinkedIn often returns partial info — fill in any blanks manually.

---

## Editing & Deleting

- **Double-click** any row in the table to open it for editing.
- Or select a row and click **✏ Edit** / **🗑 Delete**.

---

## Searching

The **🔎 search box** in the top-right corner filters the table live as you type. It matches against:

- Company name
- Role
- Location

Press `Esc` while focused in the box to clear it.

---

## Sorting

Click any column header to sort that column **A → Z**. Click the same header again to flip to **Z → A**. The active column shows a small **▲** or **▼** arrow.

Smart sorting is built in:

- **Dates** sort chronologically (not as text).
- **Days** column sorts numerically.
- **Priority** sorts High → Medium → Low.

---

## Views

Use the **View** dropdown on the toolbar to switch between filtered views:

| View | What it shows |
|---|---|
| All | Every entry, no filtering |
| Action Needed | Rows where Next Action Date is today or earlier, sorted by priority |
| In Progress | Hides Offer and Rejected entries |
| Applied This Week | Rows applied within the last 7 days |

Search and column-sort stack on top of the active view, so you can combine them freely.

---

## Board View

Click **📋 Board View** to open a Kanban-style window where applications are grouped into columns by status. Each card shows the company, role, priority dot (red / amber / green), and follow-up indicator. Useful for a quick visual scan of where everything stands.

---

## Date & Time Pickers

Every date field in the edit dialog has a **📅** button next to it that opens a calendar:

- Use **◀ ▶** to navigate months
- Today is highlighted in teal
- **Today** button jumps to today
- **Clear** removes the date

The reminder time field has a **🕐** button that opens an hour/minute picker (24-hour format, 5-minute increments).

---

## Reminders

Reminders fire as a popup **when you launch the app**. The popup lists all reminders whose date+time has passed and weren't dismissed yet. Once shown, they're auto-dismissed so you don't see the same reminder again.

To re-arm a reminder, edit the application and change the Reminder Date or Time to a future value.

---

## Status Workflow

The recommended status progression as your application moves through the pipeline:

| Stage | Status |
|---|---|
| Just submitted | 📤 Applied |
| Recruiter has it | 🔍 Under Review |
| Interview booked | 📅 Interview Scheduled |
| Got the offer | 🎉 Offer |
| They passed | ❌ Rejected |
| Crickets | 🔇 No Response |

Status drives the **In Progress** view (which hides Offer + Rejected) and the **Board View** columns. The table also colors offers in green and rejected entries in muted grey.

---

## Compensation Tracking

Three fields help you track money:

| Field | What it's for |
|---|---|
| Budget Available | What the company has signaled they'll pay |
| My Ask | The number you're targeting |
| Negotiable? | Yes / No / Unknown — whether the offer is open to negotiation |

Use free-form text (e.g. `$120k–$150k`, `120000 USD`, `30 LPA`) — the app doesn't parse currency.

---

## Field Reference

| Field | Type | Notes |
|---|---|---|
| Company | text | Required |
| Role | text | Job title |
| Location | text | City / remote / hybrid |
| Date Applied | date | YYYY-MM-DD; calendar picker available |
| Status | select | Applied / Under Review / Interview Scheduled / Offer / Rejected / No Response |
| Source | select | LinkedIn / Company Website / Referral / Job Portal / Other |
| Contact | text | Recruiter name, email, etc. |
| Last Follow-up | date | When you last reached out |
| Next Action Date | date | Drives the Action Needed view |
| Reminder Date | date | Date for the reminder popup |
| Reminder Time | HH:MM | 24-hour time |
| Priority | select | High / Medium / Low |
| Budget Available | text | What the company is offering |
| My Ask | text | What you're targeting |
| Negotiable? | select | Yes / No / Unknown |
| Job Link | URL | Click 🔗 Open Link to launch in browser |
| Notes | text | Free-form |

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Double-click row | Edit selected entry |
| Esc (in search) | Clear search |
| Mouse wheel (in dialog) | Scroll the form |

---

## Toolbar at a Glance

| Button | What it does |
|---|---|
| ➕ Add | Open the new-application dialog |
| ✏ Edit | Edit the selected row |
| 🗑 Delete | Delete the selected row (with confirmation) |
| 🔗 Open Link | Open the selected entry's Job Link in your browser |
| 📋 Board View | Open the Kanban board |
| ❓ Help | Show this help document |
| ⟳ Update | Check GitHub for a newer version |

---

## Where Is My Data?

Everything you enter is saved to **`applications.json`** in the install directory. To back up your data, copy that one file. Nothing is sent over the network unless:

- You click **🌐 Fetch** (it fetches the URL you pasted)
- You click **⟳ Update** (it talks to GitHub via git)
