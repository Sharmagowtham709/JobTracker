"""Local Job Application Tracker — Tkinter GUI, JSON storage."""
import gzip
import io
import json
import os
import re
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from datetime import datetime, date, timedelta
from html import unescape
from html.parser import HTMLParser
from tkinter import (Tk, Toplevel, StringVar, END, ttk, messagebox, Canvas,
                     Text, Frame, Label, Button, Entry, OptionMenu,
                     LEFT, RIGHT, TOP, BOTTOM, BOTH, X, Y, W, E, N, S)
import tkinter as tk

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "applications.json")
README_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
HELP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HELP.md")
APP_DIR = os.path.dirname(os.path.abspath(__file__))

VERSION = "1.0.5"
REPO_URL = "https://github.com/Sharmagowtham709/JobTracker"
REPO_BRANCH = "main"

# Override file written by the in-app updater so the label survives restarts
# even when the released commit forgot to bump the VERSION constant above.
VERSION_OVERRIDE_FILE = os.path.join(APP_DIR, ".version")


def _load_version_override():
    try:
        with open(VERSION_OVERRIDE_FILE, "r", encoding="utf-8") as f:
            v = f.read().strip()
        return v or None
    except OSError:
        return None


_override = _load_version_override()
if _override:
    VERSION = _override
del _override

# ───────────── Theme ─────────────
THEME = {
    "bg":         "#f1f5f9",   # window background
    "surface":    "#ffffff",   # cards / panels
    "surface_alt":"#f8fafc",   # alternating row
    "border":     "#e2e8f0",
    "text":       "#0f172a",
    "muted":      "#64748b",
    "primary":    "#0d9488",   # teal (matches icon)
    "primary_hi": "#14b8a6",
    "primary_dk": "#0f766e",
    "accent":     "#2563eb",
    "danger":     "#ef4444",
    "warn":       "#f59e0b",
    "success":    "#10b981",
    "header_bg":  "#0f172a",
    "header_fg":  "#f8fafc",
}

FONT_BASE = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI Semibold", 16)
FONT_SUB = ("Segoe UI", 9)


def apply_theme(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    root.configure(bg=THEME["bg"])
    root.option_add("*Font", FONT_BASE)

    style.configure(".", background=THEME["bg"], foreground=THEME["text"], font=FONT_BASE)
    style.configure("TFrame", background=THEME["bg"])
    style.configure("Card.TFrame", background=THEME["surface"])
    style.configure("Header.TFrame", background=THEME["header_bg"])

    style.configure("TLabel", background=THEME["bg"], foreground=THEME["text"])
    style.configure("Card.TLabel", background=THEME["surface"], foreground=THEME["text"])
    style.configure("Muted.TLabel", background=THEME["bg"], foreground=THEME["muted"], font=FONT_SUB)
    style.configure("CardMuted.TLabel", background=THEME["surface"], foreground=THEME["muted"], font=FONT_SUB)
    style.configure("Title.TLabel", background=THEME["header_bg"], foreground=THEME["header_fg"], font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=THEME["header_bg"], foreground="#cbd5e1", font=FONT_SUB)
    style.configure("Section.TLabel", background=THEME["surface"], foreground=THEME["primary_dk"], font=FONT_BOLD)

    # Buttons — flat, padded
    style.configure("TButton", background=THEME["surface"], foreground=THEME["text"],
                    borderwidth=1, focusthickness=0, padding=(10, 5))
    style.map("TButton",
              background=[("active", THEME["border"]), ("pressed", THEME["border"])],
              bordercolor=[("focus", THEME["primary"])])

    style.configure("Primary.TButton", background=THEME["primary"], foreground="white",
                    borderwidth=0, padding=(12, 6), font=FONT_BOLD)
    style.map("Primary.TButton",
              background=[("active", THEME["primary_hi"]), ("pressed", THEME["primary_dk"])])

    style.configure("Danger.TButton", background=THEME["danger"], foreground="white",
                    borderwidth=0, padding=(10, 5))
    style.map("Danger.TButton", background=[("active", "#dc2626"), ("pressed", "#b91c1c")])

    style.configure("Ghost.TButton", background=THEME["bg"], foreground=THEME["text"],
                    borderwidth=0, padding=(8, 5))
    style.map("Ghost.TButton",
              background=[("active", THEME["border"])])

    # Entries / Combos
    style.configure("TEntry",
                    fieldbackground=THEME["surface"], foreground=THEME["text"],
                    bordercolor=THEME["border"], lightcolor=THEME["border"],
                    darkcolor=THEME["border"], padding=4)
    style.map("TEntry", bordercolor=[("focus", THEME["primary"])])
    style.configure("TCombobox",
                    fieldbackground=THEME["surface"], background=THEME["surface"],
                    foreground=THEME["text"], bordercolor=THEME["border"],
                    arrowcolor=THEME["muted"], padding=3)
    style.map("TCombobox",
              fieldbackground=[("readonly", THEME["surface"])],
              bordercolor=[("focus", THEME["primary"])])

    # Treeview — taller rows, modern heading
    style.configure("Treeview",
                    background=THEME["surface"], fieldbackground=THEME["surface"],
                    foreground=THEME["text"], rowheight=28,
                    bordercolor=THEME["border"], borderwidth=0)
    style.configure("Treeview.Heading",
                    background=THEME["header_bg"], foreground=THEME["header_fg"],
                    relief="flat", padding=(8, 6), font=FONT_BOLD)
    style.map("Treeview.Heading",
              background=[("active", "#1e293b")])
    style.map("Treeview",
              background=[("selected", THEME["primary"])],
              foreground=[("selected", "white")])

    style.configure("TSeparator", background=THEME["border"])
    style.configure("Vertical.TScrollbar", background=THEME["bg"], troughcolor=THEME["bg"],
                    bordercolor=THEME["bg"], arrowcolor=THEME["muted"])
    style.configure("Horizontal.TScrollbar", background=THEME["bg"], troughcolor=THEME["bg"],
                    bordercolor=THEME["bg"], arrowcolor=THEME["muted"])



STATUS_OPTIONS = [
    "📤 Applied",
    "🔍 Under Review",
    "📅 Interview Scheduled",
    "🎉 Offer",
    "❌ Rejected",
    "🔇 No Response",
]
SOURCE_OPTIONS = ["LinkedIn", "Company Website", "Referral", "Job Portal", "Other"]
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
PRIORITY_RANK = {"High": 0, "Medium": 1, "Low": 2}

FIELDS = [
    # ─── Section 1: Auto-fillable from a job URL ───
    ("__section__",     "🌐 From Job URL (auto-fillable)", "section"),
    ("job_link",        "Job Link (URL)",    "entry"),
    ("company",         "Company *",         "entry"),
    ("role",            "Role",              "entry"),
    ("location",        "Location",          "entry"),
    ("source",          "Source",            "select_source"),
    ("notes",           "Notes",             "text"),

    # ─── Section 2: Manual entry ───
    ("__section2__",    "✍ Your Tracking Info (manual)", "section"),
    ("date_applied",    "Date Applied",      "date"),
    ("status",          "Status",            "select_status"),
    ("priority",        "Priority",          "select_priority"),
    ("contact",         "Contact",           "entry"),
    ("last_followup",   "Last Follow-up",    "date"),
    ("next_action",     "Next Action Date",  "date"),
    ("reminder_date",   "Reminder Date",     "date"),
    ("reminder_time",   "Reminder Time (HH:MM)", "entry"),
    ("budget_available", "Budget Available", "entry"),
    ("my_ask",          "My Ask",            "entry"),
    ("negotiable",      "Negotiable?",       "select_bool"),
]

BOOL_OPTIONS = ["Yes", "No", "Unknown"]


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_data(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def today_str():
    return date.today().isoformat()


def days_since_applied(item):
    d = parse_date(item.get("date_applied", ""))
    if not d:
        return ""
    return (date.today() - d).days


def followup_needed(item):
    d = parse_date(item.get("next_action", ""))
    if not d:
        return "—"
    return "⚠ Follow up" if d <= date.today() else "⏳ Waiting"


# ───────────── Job URL fetcher ─────────────
class _MetaParser(HTMLParser):
    """Collects og:* / twitter:* meta tags, <title>, and JSON-LD script blocks."""
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.title_parts = []
        self._in_title = False
        self.jsonld_blocks = []
        self._in_jsonld = False
        self._jsonld_buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            content = a.get("content")
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag == "title":
            self._in_title = True
        elif tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_jsonld = True
            self._jsonld_buf = []

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_jsonld:
            self.jsonld_blocks.append("".join(self._jsonld_buf))
            self._in_jsonld = False
            self._jsonld_buf = []

    def handle_data(self, data):
        if self._in_title:
            self.title_parts.append(data)
        if self._in_jsonld:
            self._jsonld_buf.append(data)


def _http_get(url, timeout=15):
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        elif resp.headers.get("Content-Encoding") == "deflate":
            import zlib
            raw = zlib.decompress(raw)
        charset = resp.headers.get_content_charset() or "utf-8"
        try:
            return raw.decode(charset, errors="replace")
        except LookupError:
            return raw.decode("utf-8", errors="replace")


def _walk_jsonld(node, results):
    if isinstance(node, list):
        for n in node:
            _walk_jsonld(n, results)
    elif isinstance(node, dict):
        t = node.get("@type")
        types = t if isinstance(t, list) else [t]
        if "JobPosting" in types:
            results.append(node)
        for v in node.values():
            _walk_jsonld(v, results)


def _format_location(loc):
    if not loc:
        return ""
    if isinstance(loc, list):
        return ", ".join(filter(None, [_format_location(x) for x in loc]))
    if isinstance(loc, dict):
        addr = loc.get("address") or loc
        if isinstance(addr, dict):
            parts = [addr.get("addressLocality"), addr.get("addressRegion"),
                     addr.get("addressCountry")]
            parts = [p["name"] if isinstance(p, dict) else p for p in parts if p]
            return ", ".join(parts)
        return str(addr)
    return str(loc)


def _strip_html(s):
    if not s:
        return ""
    return unescape(re.sub(r"<[^>]+>", " ", s)).strip()


def fetch_job_details(url):
    """Best-effort scrape: returns dict with company/role/location/source/job_link/notes."""
    out = {"job_link": url}
    host = urllib.parse.urlparse(url).netloc.lower()
    if "linkedin.com" in host:
        out["source"] = "LinkedIn"
    else:
        out["source"] = "Company Website"

    html = _http_get(url)
    parser = _MetaParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    # Try JSON-LD JobPosting first (LinkedIn, many ATS sites)
    for block in parser.jsonld_blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        postings = []
        _walk_jsonld(data, postings)
        if postings:
            jp = postings[0]
            org = jp.get("hiringOrganization") or {}
            if isinstance(org, dict):
                out["company"] = out.get("company") or org.get("name") or ""
            elif isinstance(org, str):
                out["company"] = out.get("company") or org
            out["role"] = out.get("role") or jp.get("title") or ""
            loc = _format_location(jp.get("jobLocation"))
            if loc:
                out["location"] = loc
            desc = _strip_html(jp.get("description") or "")
            if desc:
                out["notes"] = desc[:500] + ("…" if len(desc) > 500 else "")
            break

    # Fallback to OpenGraph / title
    if not out.get("role"):
        og_title = parser.meta.get("og:title") or "".join(parser.title_parts).strip()
        og_title = unescape(og_title) if og_title else ""
        if og_title:
            cleaned = re.sub(r"\s*\|\s*LinkedIn.*$", "", og_title).strip()
            # LinkedIn pattern: "{Company} hiring {Role} in {Location}"
            m = re.match(r"^(.+?)\s+hiring\s+(.+?)(?:\s+in\s+(.+))?$", cleaned, re.I)
            if m:
                if not out.get("company"):
                    out["company"] = m.group(1).strip()
                out["role"] = m.group(2).strip()
                if m.group(3) and not out.get("location"):
                    out["location"] = m.group(3).strip()
            elif " - " in cleaned and not out.get("company"):
                role, _, company = cleaned.partition(" - ")
                out["role"] = role.strip()
                out["company"] = company.strip()
            else:
                out["role"] = cleaned
    if not out.get("company"):
        site = parser.meta.get("og:site_name")
        if site and "linkedin" not in site.lower():
            out["company"] = site
    if not out.get("notes"):
        desc = parser.meta.get("og:description") or parser.meta.get("description")
        if desc:
            out["notes"] = desc.strip()

    return out


# ───────────── Date / Time Pickers ─────────────
import calendar as _cal


class DatePicker(Toplevel):
    """Popup calendar. On day click, sets `var` to YYYY-MM-DD and closes."""
    def __init__(self, master, var):
        super().__init__(master)
        self.var = var
        self.title("Pick date")
        self.resizable(False, False)
        self.transient(master)
        try:
            self.grab_set()
        except Exception:
            pass

        cur = parse_date(var.get()) or date.today()
        self.year = cur.year
        self.month = cur.month
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()
        self.configure(bg=THEME["surface"])
        nav = tk.Frame(self, bg=THEME["surface"], padx=10, pady=8)
        nav.pack(fill=X)
        tk.Button(nav, text="◀", width=3, bd=0, bg=THEME["surface"],
                  activebackground=THEME["border"], fg=THEME["text"],
                  font=FONT_BOLD, command=self._prev).pack(side=LEFT)
        tk.Label(nav, text=f"{_cal.month_name[self.month]} {self.year}",
                 font=FONT_BOLD, bg=THEME["surface"], fg=THEME["text"]
                 ).pack(side=LEFT, expand=True)
        tk.Button(nav, text="▶", width=3, bd=0, bg=THEME["surface"],
                  activebackground=THEME["border"], fg=THEME["text"],
                  font=FONT_BOLD, command=self._next).pack(side=LEFT)

        grid = tk.Frame(self, bg=THEME["surface"], padx=10, pady=4)
        grid.pack()
        for i, d in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            tk.Label(grid, text=d, width=4, bg=THEME["surface"],
                     fg=THEME["muted"], font=FONT_SUB).grid(row=0, column=i)

        today = date.today()
        weeks = _cal.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)
        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                d = date(self.year, self.month, day)
                fg = THEME["text"]
                bg = THEME["surface"]
                active = THEME["border"]
                font = FONT_BASE
                if d == today:
                    bg = THEME["primary"]
                    fg = "white"
                    active = THEME["primary_hi"]
                    font = FONT_BOLD
                tk.Button(grid, text=str(day), width=4, bd=0,
                          bg=bg, fg=fg, activebackground=active,
                          activeforeground=fg, font=font,
                          command=lambda dd=d: self._pick(dd)
                          ).grid(row=r, column=c, padx=1, pady=1)

        foot = tk.Frame(self, bg=THEME["surface"], padx=10, pady=8)
        foot.pack(fill=X)
        ttk.Button(foot, text="Today",
                   command=lambda: self._pick(date.today())).pack(side=LEFT, padx=(0, 6))
        ttk.Button(foot, text="Clear", command=self._clear).pack(side=LEFT)
        ttk.Button(foot, text="Cancel", command=self.destroy).pack(side=RIGHT)

    def _prev(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._build()

    def _next(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._build()

    def _pick(self, d):
        self.var.set(d.isoformat())
        self.destroy()

    def _clear(self):
        self.var.set("")
        self.destroy()


class TimePicker(Toplevel):
    """Popup HH:MM picker."""
    def __init__(self, master, var):
        super().__init__(master)
        self.var = var
        self.title("Pick time")
        self.resizable(False, False)
        self.transient(master)
        try:
            self.grab_set()
        except Exception:
            pass

        cur = var.get() or "10:00"
        try:
            h, m = cur.split(":")
            h, m = int(h), int(m)
        except (ValueError, AttributeError):
            h, m = 10, 0

        self.configure(bg=THEME["surface"])
        body = tk.Frame(self, bg=THEME["surface"], padx=18, pady=14)
        body.pack()
        tk.Label(body, text="Hour", bg=THEME["surface"], fg=THEME["muted"],
                 font=FONT_SUB).grid(row=0, column=0)
        tk.Label(body, text="Min", bg=THEME["surface"], fg=THEME["muted"],
                 font=FONT_SUB).grid(row=0, column=2)
        self.h = ttk.Spinbox(body, from_=0, to=23, width=4, format="%02.0f")
        self.h.set(f"{h:02d}")
        self.h.grid(row=1, column=0, padx=2, pady=4)
        tk.Label(body, text=":", font=("Segoe UI", 16, "bold"),
                 bg=THEME["surface"], fg=THEME["text"]).grid(row=1, column=1, padx=6)
        self.m = ttk.Spinbox(body, from_=0, to=59, width=4, format="%02.0f", increment=5)
        self.m.set(f"{m:02d}")
        self.m.grid(row=1, column=2, padx=2, pady=4)

        btns = tk.Frame(self, bg=THEME["surface"], pady=8, padx=14)
        btns.pack(fill=X)
        ttk.Button(btns, text="OK", style="Primary.TButton",
                   command=self._ok).pack(side=RIGHT, padx=(6, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=RIGHT)

    def _ok(self):
        try:
            hh = int(self.h.get())
            mm = int(self.m.get())
            self.var.set(f"{hh:02d}:{mm:02d}")
            self.destroy()
        except ValueError:
            pass


def make_picker_field(parent, var, kind):
    """Returns a Frame containing an Entry + a 📅/🕐 button that opens the picker."""
    frame = ttk.Frame(parent)
    ttk.Entry(frame, textvariable=var).pack(side=LEFT, fill=X, expand=True)
    icon = "📅" if kind == "date" else "🕐"
    cls = DatePicker if kind == "date" else TimePicker
    ttk.Button(frame, text=icon, width=3,
               command=lambda: cls(parent.winfo_toplevel(), var)
               ).pack(side=LEFT, padx=(4, 0))
    return frame


# ───────────── Add / Edit Dialog ─────────────
class EditDialog(Toplevel):
    def __init__(self, master, app, item=None, on_save=None):
        super().__init__(master)
        self.title("Edit Application" if item else "New Application")
        self.app = app
        self.on_save = on_save
        self.item = item or {}
        self.vars = {}
        self.geometry("620x780")
        self.configure(bg=THEME["bg"])

        # Header
        header = ttk.Frame(self, style="Header.TFrame", padding=(16, 10))
        header.pack(fill=X)
        ttk.Label(header,
                  text=("✏  Edit Application" if item else "➕  New Application"),
                  style="Title.TLabel").pack(side=LEFT)

        # URL fetch bar (card)
        url_card = ttk.Frame(self, padding=(14, 12, 14, 6))
        url_card.pack(fill=X)
        ttk.Label(url_card, text="🌐 Paste a job URL to auto-fill",
                  style="Section.TLabel").pack(anchor=W, pady=(0, 6))
        url_row = ttk.Frame(url_card)
        url_row.pack(fill=X)
        self.url_var = StringVar(value=self.item.get("job_link", ""))
        ttk.Entry(url_row, textvariable=self.url_var).pack(
            side=LEFT, fill=X, expand=True, ipady=2)
        self.fetch_btn = ttk.Button(url_row, text="🌐  Fetch",
                                    style="Primary.TButton", command=self._fetch_url)
        self.fetch_btn.pack(side=LEFT, padx=(8, 0))

        # Scrollable form container
        form_outer = ttk.Frame(self, padding=(14, 4, 14, 4))
        form_outer.pack(fill=BOTH, expand=True)
        canvas = tk.Canvas(form_outer, bg=THEME["bg"], highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(form_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        container = ttk.Frame(canvas)
        canvas_win = canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind("<Configure>",
                       lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(canvas_win, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-int(e.delta / 120), "units"))

        for i, (key, label, kind) in enumerate(FIELDS):
            if kind == "section":
                ttk.Label(container, text=label, style="Section.TLabel"
                          ).grid(row=i, column=0, columnspan=3,
                                 sticky=W+E, pady=(14, 4))
                ttk.Separator(container, orient="horizontal").grid(
                    row=i, column=0, columnspan=3, sticky=W+E, pady=(0, 4))
                continue
            ttk.Label(container, text=label).grid(
                row=i, column=0, sticky=W, pady=4, padx=(2, 10))
            val = self.item.get(key, "")
            if kind == "select_status":
                var = StringVar(value=val or STATUS_OPTIONS[0])
                ttk.Combobox(container, textvariable=var, values=STATUS_OPTIONS,
                             state="readonly").grid(row=i, column=1, sticky=W+E, pady=4)
            elif kind == "select_source":
                var = StringVar(value=val or SOURCE_OPTIONS[0])
                ttk.Combobox(container, textvariable=var, values=SOURCE_OPTIONS,
                             state="readonly").grid(row=i, column=1, sticky=W+E, pady=4)
            elif kind == "select_priority":
                var = StringVar(value=val or "Medium")
                ttk.Combobox(container, textvariable=var, values=PRIORITY_OPTIONS,
                             state="readonly").grid(row=i, column=1, sticky=W+E, pady=4)
            elif kind == "select_bool":
                var = StringVar(value=val or "Unknown")
                ttk.Combobox(container, textvariable=var, values=BOOL_OPTIONS,
                             state="readonly").grid(row=i, column=1, sticky=W+E, pady=4)
            elif kind == "text":
                txt = Text(container, height=5, wrap="word",
                           bg=THEME["surface"], fg=THEME["text"],
                           relief="solid", bd=1, highlightthickness=0,
                           font=FONT_BASE, padx=6, pady=4)
                txt.insert("1.0", val)
                txt.grid(row=i, column=1, sticky=W+E, pady=4)
                self.vars[key] = ("text", txt)
                continue
            elif kind == "date":
                var = StringVar(value=val)
                make_picker_field(container, var, "date").grid(
                    row=i, column=1, sticky=W+E, pady=4)
                ttk.Label(container, text="YYYY-MM-DD", style="Muted.TLabel").grid(
                    row=i, column=2, sticky=W, padx=(8, 2))
            else:
                var = StringVar(value=val)
                if key == "reminder_time":
                    make_picker_field(container, var, "time").grid(
                        row=i, column=1, sticky=W+E, pady=4)
                else:
                    ttk.Entry(container, textvariable=var).grid(
                        row=i, column=1, sticky=W+E, pady=4)
            self.vars[key] = ("var", var)

        container.columnconfigure(1, weight=1)

        # Suggestion: when new, prefill smart defaults
        if not item:
            self._prefill_defaults()

        btns = ttk.Frame(self, padding=(14, 10))
        btns.pack(fill=X)
        ttk.Button(btns, text="💾  Save", style="Primary.TButton",
                   command=self._save).pack(side=RIGHT, padx=(8, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=RIGHT)

    def _fetch_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showinfo("URL needed", "Paste a job URL first.", parent=self)
            return
        if not re.match(r"^https?://", url):
            url = "https://" + url
            self.url_var.set(url)
        self.fetch_btn.config(text="⏳ …", state="disabled")

        def worker():
            try:
                data = fetch_job_details(url)
                err = None
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                data, err = None, f"Network error: {e}"
            except Exception as e:
                data, err = None, f"{type(e).__name__}: {e}"
            self.after(0, lambda: self._apply_fetched(data, err))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_fetched(self, data, err):
        self.fetch_btn.config(text="🌐 Fetch", state="normal")
        if err or not data:
            messagebox.showwarning("Fetch failed",
                                   err or "No details extracted. Fill manually.",
                                   parent=self)
            return
        filled = []
        for key in ("company", "role", "location", "source", "job_link", "notes"):
            val = data.get(key)
            if not val:
                continue
            kind, widget = self.vars.get(key, (None, None))
            if not widget:
                continue
            if kind == "text":
                if not widget.get("1.0", END).strip():
                    widget.insert("1.0", val)
                    filled.append(key)
            else:
                if not widget.get():
                    widget.set(val)
                    filled.append(key)
        if filled:
            messagebox.showinfo("Fetched",
                                f"Auto-filled: {', '.join(filled)}.\nReview and adjust.",
                                parent=self)
        else:
            messagebox.showinfo("Fetched",
                                "No new fields filled (existing values kept).",
                                parent=self)

    def _prefill_defaults(self):
        if self.vars["date_applied"][1].get() == "":
            self.vars["date_applied"][1].set(today_str())
        if self.vars["next_action"][1].get() == "":
            self.vars["next_action"][1].set((date.today() + timedelta(days=6)).isoformat())
        if self.vars["reminder_date"][1].get() == "":
            self.vars["reminder_date"][1].set((date.today() + timedelta(days=6)).isoformat())
        if self.vars["reminder_time"][1].get() == "":
            self.vars["reminder_time"][1].set("10:00")

    def _save(self):
        data = dict(self.item)
        for key, (kind, widget) in self.vars.items():
            data[key] = widget.get("1.0", END).strip() if kind == "text" else widget.get().strip()

        if not data.get("company"):
            messagebox.showwarning("Missing", "Company is required.", parent=self)
            return

        for dkey in ("date_applied", "last_followup", "next_action", "reminder_date"):
            v = data.get(dkey, "")
            if v and parse_date(v) is None:
                messagebox.showwarning("Invalid date", f"{dkey} must be YYYY-MM-DD.", parent=self)
                return

        rt = data.get("reminder_time", "")
        if rt:
            try:
                datetime.strptime(rt, "%H:%M")
            except ValueError:
                messagebox.showwarning("Invalid time", "Reminder time must be HH:MM.", parent=self)
                return

        if "id" not in data:
            data["id"] = str(uuid.uuid4())
            data["reminder_dismissed"] = False
        if self.on_save:
            self.on_save(data)
        self.destroy()


# ───────────── Board View ─────────────
class BoardView(Toplevel):
    def __init__(self, master, items):
        super().__init__(master)
        self.title("Board View — grouped by Status")
        self.geometry("1280x640")
        self.configure(bg=THEME["bg"])

        header = ttk.Frame(self, style="Header.TFrame", padding=(16, 10))
        header.pack(fill=X)
        ttk.Label(header, text="📋  Board View", style="Title.TLabel").pack(side=LEFT)

        outer = ttk.Frame(self, padding=10)
        outer.pack(fill=BOTH, expand=True)

        for status in STATUS_OPTIONS:
            col = tk.Frame(outer, bg=THEME["surface"], bd=0,
                           highlightbackground=THEME["border"], highlightthickness=1)
            col.pack(side=LEFT, fill=Y, padx=6, pady=4, ipadx=6, ipady=6)
            count = sum(1 for it in items if it.get("status") == status)
            tk.Label(col, text=f"{status}  ({count})",
                     font=FONT_BOLD, bg=THEME["surface"], fg=THEME["text"]
                     ).pack(anchor=W, pady=(4, 8), padx=4)
            for it in items:
                if it.get("status") != status:
                    continue
                card = tk.Frame(col, bg=THEME["surface_alt"], bd=0,
                                highlightbackground=THEME["border"], highlightthickness=1)
                card.pack(fill=X, pady=4, padx=4, ipadx=6, ipady=6)
                tk.Label(card, text=it.get("company", "") or "—",
                         font=FONT_BOLD, bg=THEME["surface_alt"],
                         fg=THEME["text"]).pack(anchor=W)
                tk.Label(card, text=it.get("role", ""), bg=THEME["surface_alt"],
                         fg=THEME["muted"], font=FONT_SUB).pack(anchor=W)
                pr = it.get("priority", "")
                pr_color = {"High": THEME["danger"], "Medium": THEME["warn"],
                            "Low": THEME["success"]}.get(pr, THEME["muted"])
                meta = tk.Frame(card, bg=THEME["surface_alt"])
                meta.pack(fill=X, pady=(4, 0))
                tk.Label(meta, text=f"● {pr or '—'}", bg=THEME["surface_alt"],
                         fg=pr_color, font=FONT_SUB).pack(side=LEFT)
                tk.Label(meta, text=f"  {followup_needed(it)}",
                         bg=THEME["surface_alt"], fg=THEME["muted"],
                         font=FONT_SUB).pack(side=LEFT)


# ───────────── Help dialog (renders README.md) ─────────────
class HelpDialog(Toplevel):
    """Simple in-app help that renders README.md with basic markdown styling."""
    def __init__(self, master):
        super().__init__(master)
        self.title("Help · Job Application Tracker")
        self.geometry("780x680")
        self.configure(bg=THEME["bg"])
        self.transient(master)

        header = ttk.Frame(self, style="Header.TFrame", padding=(16, 10))
        header.pack(fill=X)
        ttk.Label(header, text="❓  Help & Documentation", style="Title.TLabel").pack(side=LEFT)

        body = ttk.Frame(self, padding=(12, 8))
        body.pack(fill=BOTH, expand=True)

        text = Text(body, wrap="word", bg=THEME["surface"], fg=THEME["text"],
                    relief="flat", bd=0, padx=18, pady=14, spacing1=2, spacing3=4,
                    font=FONT_BASE)
        sb = ttk.Scrollbar(body, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=sb.set)
        text.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        # Markdown styling tags
        text.tag_configure("h1", font=("Segoe UI", 18, "bold"),
                           foreground=THEME["primary_dk"], spacing1=14, spacing3=6)
        text.tag_configure("h2", font=("Segoe UI", 14, "bold"),
                           foreground=THEME["text"], spacing1=12, spacing3=4)
        text.tag_configure("h3", font=("Segoe UI", 11, "bold"),
                           foreground=THEME["text"], spacing1=8, spacing3=3)
        text.tag_configure("bold", font=FONT_BOLD)
        text.tag_configure("italic", font=("Segoe UI", 10, "italic"))
        text.tag_configure("code", font=("Consolas", 10),
                           background="#f1f5f9", foreground="#be185d")
        text.tag_configure("codeblock", font=("Consolas", 10),
                           background="#0f172a", foreground="#e2e8f0",
                           lmargin1=20, lmargin2=20, spacing1=6, spacing3=6)
        text.tag_configure("bullet", lmargin1=18, lmargin2=36, spacing1=2)
        text.tag_configure("link", foreground=THEME["accent"], underline=True)
        text.tag_configure("hr", foreground=THEME["border"])
        text.tag_configure("muted", foreground=THEME["muted"], font=FONT_SUB)
        text.tag_configure("quote", foreground=THEME["muted"],
                           font=("Segoe UI", 10, "italic"),
                           lmargin1=18, lmargin2=18, spacing1=4, spacing3=4,
                           background="#f8fafc")
        # Table tags — monospaced grid
        text.tag_configure("tbl_head", font=("Consolas", 10, "bold"),
                           foreground=THEME["text"], background="#e2e8f0",
                           lmargin1=8, lmargin2=8)
        text.tag_configure("tbl_sep", font=("Consolas", 10),
                           foreground=THEME["border"],
                           lmargin1=8, lmargin2=8)
        text.tag_configure("tbl_row", font=("Consolas", 10),
                           foreground=THEME["text"], background=THEME["surface"],
                           lmargin1=8, lmargin2=8)
        text.tag_configure("tbl_alt", font=("Consolas", 10),
                           foreground=THEME["text"], background=THEME["surface_alt"],
                           lmargin1=8, lmargin2=8)

        self._render(text)
        text.configure(state="disabled")

        foot = ttk.Frame(self, padding=(14, 8))
        foot.pack(fill=X)
        ttk.Label(foot, style="Muted.TLabel",
                  text=f"v{VERSION} · {REPO_URL}").pack(side=LEFT)
        ttk.Button(foot, text="Open repo on GitHub",
                   command=lambda: webbrowser.open(REPO_URL)).pack(side=RIGHT, padx=(6, 0))
        ttk.Button(foot, text="Close", command=self.destroy).pack(side=RIGHT)

    def _render(self, text):
        # Prefer HELP.md (curated app help); fall back to README.md if missing.
        path = HELP_FILE if os.path.exists(HELP_FILE) else README_FILE
        if not os.path.exists(path):
            text.insert(END, "Help file not found.\n", "muted")
            text.insert(END, f"\nLooked for:\n  {HELP_FILE}\n  {README_FILE}\n", "muted")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError as e:
            text.insert(END, f"Failed to read help: {e}\n", "muted")
            return

        in_code = False
        i = 0
        while i < len(lines):
            raw = lines[i]
            line = raw.rstrip()
            if line.startswith("```"):
                in_code = not in_code
                text.insert(END, "\n")
                i += 1
                continue
            if in_code:
                text.insert(END, line + "\n", "codeblock")
                i += 1
                continue
            # Markdown table: line starts with | and the next line is a |---|---| separator
            if (line.lstrip().startswith("|")
                    and i + 1 < len(lines)
                    and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1])):
                table, consumed = self._collect_table(lines, i)
                self._render_table(text, table)
                i += consumed
                continue
            if not line:
                text.insert(END, "\n")
            elif line.startswith("# "):
                text.insert(END, line[2:] + "\n", "h1")
            elif line.startswith("## "):
                text.insert(END, line[3:] + "\n", "h2")
            elif line.startswith("### "):
                text.insert(END, line[4:] + "\n", "h3")
            elif line.startswith("> "):
                self._render_inline(text, line[2:].strip(), "quote")
                text.insert(END, "\n")
            elif re.match(r"^[-*]\s", line):
                text.insert(END, "  • ", "bullet")
                self._render_inline(text, line[2:].strip(), "bullet")
                text.insert(END, "\n")
            elif re.match(r"^\d+\.\s", line):
                text.insert(END, "  ", "bullet")
                self._render_inline(text, line, "bullet")
                text.insert(END, "\n")
            elif line.strip() in ("---", "***", "___"):
                text.insert(END, "─" * 80 + "\n", "hr")
            else:
                self._render_inline(text, line, None)
                text.insert(END, "\n")
            i += 1

    @staticmethod
    def _split_row(line):
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    def _collect_table(self, lines, start):
        """Returns (rows, lines_consumed). rows[0] = header, rest = body."""
        header = self._split_row(lines[start])
        rows = [header]
        i = start + 2  # skip header + separator row
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            rows.append(self._split_row(lines[i]))
            i += 1
        return rows, i - start

    def _render_table(self, text, rows):
        if not rows:
            return
        ncols = max(len(r) for r in rows)
        rows = [r + [""] * (ncols - len(r)) for r in rows]
        # column widths from longest plain-text cell
        widths = [max(len(self._strip_md(r[c])) for r in rows) for c in range(ncols)]
        widths = [max(w, 4) for w in widths]
        text.insert(END, "\n")
        for ridx, row in enumerate(rows):
            tag = "tbl_head" if ridx == 0 else ("tbl_alt" if ridx % 2 else "tbl_row")
            line = "  " + " │ ".join(
                self._strip_md(cell).ljust(widths[c]) for c, cell in enumerate(row)
            ) + "  "
            text.insert(END, line + "\n", tag)
            if ridx == 0:
                sep = "  " + "─┼─".join("─" * w for w in widths) + "  "
                text.insert(END, sep + "\n", "tbl_sep")
        text.insert(END, "\n")

    @staticmethod
    def _strip_md(s):
        s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
        s = re.sub(r"`([^`]+)`", r"\1", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        return s

    def _render_inline(self, text, line, base_tag):
        # Process **bold**, `code`, [text](url)
        pattern = re.compile(
            r"(\*\*[^*]+\*\*)|(`[^`]+`)|(\[[^\]]+\]\([^)]+\))"
        )
        pos = 0
        for m in pattern.finditer(line):
            if m.start() > pos:
                tags = (base_tag,) if base_tag else ()
                text.insert(END, line[pos:m.start()], tags)
            tok = m.group(0)
            if tok.startswith("**"):
                tags = ("bold",) + ((base_tag,) if base_tag else ())
                text.insert(END, tok[2:-2], tags)
            elif tok.startswith("`"):
                tags = ("code",) + ((base_tag,) if base_tag else ())
                text.insert(END, tok[1:-1], tags)
            elif tok.startswith("["):
                lm = re.match(r"\[([^\]]+)\]\(([^)]+)\)", tok)
                if lm:
                    label, url = lm.group(1), lm.group(2)
                    start = text.index(END + "-1c")
                    text.insert(END, label, ("link",))
                    end = text.index(END + "-1c")
                    tag = f"link_{abs(hash(url))}"
                    text.tag_add(tag, start, end)
                    text.tag_bind(tag, "<Button-1>",
                                  lambda _e, u=url: webbrowser.open(u))
                    text.tag_bind(tag, "<Enter>",
                                  lambda _e: text.configure(cursor="hand2"))
                    text.tag_bind(tag, "<Leave>",
                                  lambda _e: text.configure(cursor=""))
            pos = m.end()
        if pos < len(line):
            tags = (base_tag,) if base_tag else ()
            text.insert(END, line[pos:], tags)


# ───────────── Update checker (git-based) ─────────────
def _run_git(args, cwd=APP_DIR, timeout=30):
    """Run a git command; return (returncode, stdout, stderr)."""
    import subprocess
    try:
        proc = subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git not found on PATH"
    except subprocess.TimeoutExpired:
        return 124, "", "git command timed out"


def _parse_semver(s):
    """Returns a tuple like (1,0,1) for '1.0.1' / 'v1.0.1' / '1.0.1-rc1'.
    Returns None if it doesn't look like semver."""
    if not s:
        return None
    s = s.strip().lstrip("vV")
    s = s.split("-", 1)[0].split("+", 1)[0]  # strip prerelease / build
    parts = s.split(".")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])


def _latest_remote_tag():
    """Query the remote for the highest semver tag. Returns (tag_str, semver) or (None, None)."""
    rc, out, _ = _run_git(["ls-remote", "--tags", "--refs", "origin"])
    if rc != 0 or not out:
        return None, None
    best_tag, best_ver = None, None
    for line in out.splitlines():
        # line: "<sha>\trefs/tags/<tag>"
        parts = line.split("refs/tags/")
        if len(parts) != 2:
            continue
        tag = parts[1].strip()
        ver = _parse_semver(tag)
        if ver is None:
            continue
        if best_ver is None or ver > best_ver:
            best_tag, best_ver = tag, ver
    return best_tag, best_ver


def check_updates():
    """Returns dict: {ok, is_git, behind, current, latest, message}.
    Compares the local VERSION constant to the highest semver tag on the remote."""
    if not os.path.isdir(os.path.join(APP_DIR, ".git")):
        return {"ok": False, "is_git": False,
                "message": ("This install is not a git checkout, so the Update "
                            "button can't auto-pull.\n\nReinstall by cloning:\n"
                            f"git clone {REPO_URL}")}

    rc, _, err = _run_git(["fetch", "--tags", "--prune", "--quiet"])
    if rc != 0:
        return {"ok": False, "is_git": True,
                "message": f"git fetch failed:\n{err or 'unknown error'}"}

    latest_tag, latest_ver = _latest_remote_tag()
    local_ver = _parse_semver(VERSION)

    if latest_tag is None or latest_ver is None:
        # No release tags published — fall back to commit comparison on the branch.
        rc1, local_sha, _ = _run_git(["rev-parse", "HEAD"])
        rc2, remote_sha, _ = _run_git(["rev-parse", f"origin/{REPO_BRANCH}"])
        if rc1 != 0 or rc2 != 0:
            return {"ok": False, "is_git": True,
                    "message": "Could not read git revisions."}
        if local_sha == remote_sha:
            return {"ok": True, "is_git": True, "behind": 0,
                    "current": VERSION, "latest": VERSION,
                    "message": f"You're up to date (v{VERSION}). No release tags published yet."}
        rc, count, _ = _run_git(
            ["rev-list", "--count", f"HEAD..origin/{REPO_BRANCH}"])
        behind = int(count) if rc == 0 and count.isdigit() else 1
        return {"ok": True, "is_git": True, "behind": behind,
                "current": VERSION, "latest": f"main@{remote_sha[:7]}",
                "message": f"{behind} new commit(s) on {REPO_BRANCH} "
                           f"(no tagged release found)."}

    if local_ver is None:
        return {"ok": True, "is_git": True, "behind": 1,
                "current": VERSION, "latest": latest_tag,
                "message": f"Latest release: v{latest_tag}. Local VERSION "
                           f"({VERSION!r}) doesn't parse as semver."}

    if latest_ver <= local_ver:
        return {"ok": True, "is_git": True, "behind": 0,
                "current": VERSION, "latest": latest_tag,
                "message": f"You're up to date (v{VERSION}). "
                           f"Latest release: v{latest_tag}."}

    return {"ok": True, "is_git": True, "behind": 1,
            "current": VERSION, "latest": latest_tag,
            "message": f"New version available: v{latest_tag} "
                       f"(you have v{VERSION})."}


def apply_update():
    """Pull latest commits from the tracked branch (which includes the new tag).
    Returns (ok, new_version_or_message)."""
    rc, _, err = _run_git(["pull", "--ff-only", "origin", REPO_BRANCH])
    if rc != 0:
        return False, err or "git pull failed"
    new_ver = _read_version_from_disk() or VERSION
    return True, new_ver


def restart_app(root):
    """Relaunch this script in a fresh process and exit the current one."""
    import subprocess, sys
    script = os.path.abspath(__file__)
    try:
        subprocess.Popen([sys.executable, script], cwd=APP_DIR, close_fds=True)
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass
    os._exit(0)


def _read_version_from_disk():
    """Parse the VERSION constant out of tracker.py on disk (post-pull)."""
    path = os.path.abspath(__file__)
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\s*VERSION\s*=\s*["\']([^"\']+)["\']', line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return None


# ───────────── Main App ─────────────
class TrackerApp:
    VIEWS = ["All", "Action Needed", "In Progress", "Applied This Week"]

    def __init__(self, root):
        self.root = root
        root.title("Job Application Tracker")
        root.geometry("1320x720")
        apply_theme(root)

        self.items = load_data()
        self.current_view = StringVar(value="All")
        self.search_var = StringVar()
        self.sort_col = None
        self.sort_reverse = False

        # Header banner
        header = ttk.Frame(root, style="Header.TFrame", padding=(18, 12))
        header.pack(fill=X)
        ttk.Label(header, text="📋  Job Application Tracker", style="Title.TLabel").pack(side=LEFT)
        ttk.Label(header, text="Lightweight CRM for your job hunt", style="Subtitle.TLabel"
                  ).pack(side=LEFT, padx=(12, 0), pady=(6, 0))

        # Toolbar (card)
        toolbar = ttk.Frame(root, padding=(12, 10))
        toolbar.pack(fill=X)
        ttk.Button(toolbar, text="➕  Add", style="Primary.TButton",
                   command=self.add_item).pack(side=LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="✏  Edit", command=self.edit_item).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="🗑  Delete", style="Danger.TButton",
                   command=self.delete_item).pack(side=LEFT, padx=3)
        ttk.Separator(toolbar, orient="vertical").pack(side=LEFT, fill=Y, padx=8)
        ttk.Button(toolbar, text="🔗  Open Link", command=self.open_link).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="📋  Board View", command=self.show_board).pack(side=LEFT, padx=3)
        ttk.Button(toolbar, text="❓  Help", command=self.show_help).pack(side=LEFT, padx=3)

        ttk.Label(toolbar, text="View:", style="Muted.TLabel").pack(side=LEFT, padx=(20, 4))
        view_cb = ttk.Combobox(toolbar, textvariable=self.current_view,
                               values=self.VIEWS, state="readonly", width=18)
        view_cb.pack(side=LEFT)
        view_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        # Right side: search + status
        self.status_lbl = ttk.Label(toolbar, text="", style="Muted.TLabel")
        self.status_lbl.pack(side=RIGHT, padx=(10, 0))
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=28)
        search_entry.pack(side=RIGHT)
        ttk.Label(toolbar, text="🔎", style="Muted.TLabel").pack(side=RIGHT, padx=(0, 4))
        self.search_var.trace_add("write", lambda *_: self.refresh())
        search_entry.bind("<Escape>", lambda _e: (self.search_var.set(""), "break"))

        cols = ("company", "role", "location", "status", "priority",
                "date_applied", "days_since", "next_action", "followup",
                "budget_available", "my_ask", "negotiable",
                "source", "contact")
        headers = {
            "company": "Company", "role": "Role", "location": "Location",
            "status": "Status", "priority": "Priority",
            "date_applied": "Applied", "days_since": "Days",
            "next_action": "Next Action", "followup": "Follow-up?",
            "budget_available": "Budget", "my_ask": "My Ask",
            "negotiable": "Negotiable?",
            "source": "Source", "contact": "Contact",
        }
        widths = {"company": 150, "role": 150, "location": 110, "status": 160,
                  "priority": 75, "date_applied": 90, "days_since": 55,
                  "next_action": 100, "followup": 100,
                  "budget_available": 95, "my_ask": 95, "negotiable": 85,
                  "source": 105, "contact": 115}

        # Treeview card
        tree_card = ttk.Frame(root, padding=(12, 0, 12, 8))
        tree_card.pack(fill=BOTH, expand=True)
        tree_frame = ttk.Frame(tree_card, style="Card.TFrame")
        tree_frame.pack(fill=BOTH, expand=True)
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self._headers = headers
        for c in cols:
            self.tree.heading(c, text=headers[c],
                              command=lambda col=c: self._on_heading_click(col))
            self.tree.column(c, width=widths[c], minwidth=widths[c],
                             anchor=W, stretch=False)
        # Row striping + accent tags
        self.tree.tag_configure("odd", background=THEME["surface_alt"])
        self.tree.tag_configure("even", background=THEME["surface"])
        self.tree.tag_configure("offer", foreground=THEME["success"])
        self.tree.tag_configure("rejected", foreground=THEME["muted"])
        self.tree.tag_configure("urgent", foreground=THEME["danger"])
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", lambda _e: self.edit_item())

        # Bottom status bar: hint (left) + update button + version (right)
        status_bar = ttk.Frame(root, padding=(14, 6))
        status_bar.pack(fill=X)
        ttk.Label(status_bar, style="Muted.TLabel",
                  text="Tip: New entries auto-suggest Date Applied = today, "
                       "Next Action = +6 days, Reminder = +6 days @ 10:00."
                  ).pack(side=LEFT)
        self.version_lbl = ttk.Label(status_bar, style="Muted.TLabel",
                                     text=f"v{VERSION}")
        self.version_lbl.pack(side=RIGHT, padx=(8, 0))
        ttk.Button(status_bar, text="⟳  Update",
                   command=self.check_for_updates).pack(side=RIGHT)

        self.refresh()
        self.root.after(500, self.check_reminders)

    def _on_heading_click(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
        self.refresh()

    def _sort_key(self, item, col):
        if col == "days_since":
            v = days_since_applied(item)
            return (0, v) if isinstance(v, int) else (1, 0)
        if col == "followup":
            return followup_needed(item)
        if col == "priority":
            return PRIORITY_RANK.get(item.get("priority", ""), 99)
        if col in ("date_applied", "next_action"):
            d = parse_date(item.get(col, ""))
            return (1, "") if not d else (0, d.toordinal())
        return (item.get(col, "") or "").lower()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        view = self.current_view.get()
        items = list(self.items)

        if view == "Action Needed":
            items = [i for i in items
                     if (d := parse_date(i.get("next_action"))) and d <= date.today()]
            items.sort(key=lambda i: PRIORITY_RANK.get(i.get("priority", "Low"), 99))
        elif view == "In Progress":
            items = [i for i in items
                     if i.get("status") not in ("🎉 Offer", "❌ Rejected")]
        elif view == "Applied This Week":
            cutoff = date.today() - timedelta(days=7)
            items = [i for i in items
                     if (d := parse_date(i.get("date_applied"))) and d >= cutoff]

        # Search filter (matches company / role / location, case-insensitive)
        q = self.search_var.get().strip().lower()
        if q:
            items = [i for i in items
                     if q in (i.get("company", "") + " " +
                              i.get("role", "") + " " +
                              i.get("location", "")).lower()]

        # Header-driven sort overrides view default
        if self.sort_col:
            items.sort(key=lambda it: self._sort_key(it, self.sort_col),
                       reverse=self.sort_reverse)

        # Update header arrows
        for c, base in self._headers.items():
            arrow = ""
            if c == self.sort_col:
                arrow = "  ▼" if self.sort_reverse else "  ▲"
            self.tree.heading(c, text=base + arrow)

        for idx, it in enumerate(items):
            tags = ["odd" if idx % 2 else "even"]
            st = it.get("status", "")
            if "Offer" in st:
                tags.append("offer")
            elif "Rejected" in st:
                tags.append("rejected")
            if followup_needed(it).startswith("⚠"):
                tags.append("urgent")
            self.tree.insert("", END, iid=it["id"], tags=tags, values=(
                it.get("company", ""), it.get("role", ""), it.get("location", ""),
                it.get("status", ""), it.get("priority", ""),
                it.get("date_applied", ""), days_since_applied(it),
                it.get("next_action", ""), followup_needed(it),
                it.get("budget_available", ""), it.get("my_ask", ""),
                it.get("negotiable", ""),
                it.get("source", ""), it.get("contact", ""),
            ))
        self.status_lbl.config(text=f"{len(items)} shown · {len(self.items)} total")

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return next((i for i in self.items if i["id"] == sel[0]), None)

    def add_item(self):
        EditDialog(self.root, self, on_save=self._save_new)

    def _save_new(self, data):
        self.items.append(data)
        save_data(self.items)
        self.refresh()

    def edit_item(self):
        item = self._selected()
        if not item:
            messagebox.showinfo("Select", "Select an application to edit.")
            return
        EditDialog(self.root, self, item=item, on_save=self._save_existing)

    def _save_existing(self, data):
        for i, it in enumerate(self.items):
            if it["id"] == data["id"]:
                self.items[i] = data
                break
        save_data(self.items)
        self.refresh()

    def delete_item(self):
        item = self._selected()
        if not item:
            return
        if messagebox.askyesno("Delete", f"Delete application to {item.get('company')}?"):
            self.items = [i for i in self.items if i["id"] != item["id"]]
            save_data(self.items)
            self.refresh()

    def open_link(self):
        item = self._selected()
        if item and item.get("job_link"):
            webbrowser.open(item["job_link"])

    def show_board(self):
        BoardView(self.root, self.items)

    def show_help(self):
        HelpDialog(self.root)

    def check_for_updates(self):
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            info = check_updates()
        finally:
            self.root.config(cursor="")
        if not info.get("ok"):
            messagebox.showinfo("Update", info["message"], parent=self.root)
            return
        if info["behind"] == 0:
            messagebox.showinfo("Update", info["message"], parent=self.root)
            return
        old_ver = VERSION
        target = info.get("latest", "newer version")
        if not messagebox.askyesno(
                "Update available",
                f"{info['message']}\n\n"
                f"Update from v{old_ver} to v{target}?",
                parent=self.root):
            return
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            ok, result = apply_update()
        finally:
            self.root.config(cursor="")
        if not ok:
            messagebox.showerror("Update failed", result, parent=self.root)
            return
        # Prefer the tag name (what the user is updating *to*) over the
        # VERSION constant inside the pulled file — the file constant may
        # not have been bumped in the released commit.
        target = info.get("latest")
        from_disk = _read_version_from_disk()
        new_ver = target or from_disk or result
        try:
            with open(VERSION_OVERRIDE_FILE, "w", encoding="utf-8") as f:
                f.write(new_ver)
        except OSError:
            pass
        self.version_lbl.config(text=f"v{new_ver}  (restart to apply)")
        self._show_update_success(old_ver, new_ver)

    def _show_update_success(self, old_ver, new_ver):
        dlg = Toplevel(self.root)
        dlg.title("Updated")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)
        try:
            dlg.configure(bg=THEME["bg"])
        except Exception:
            pass

        body = ttk.Frame(dlg, padding=20)
        body.pack(fill=BOTH, expand=True)

        if old_ver == new_ver:
            headline = f"✅ Update pulled (v{new_ver})."
            sub = ("The pulled code reports the same version "
                   "(v{0}). If a newer release was expected, the "
                   "remote commit may not have bumped the VERSION "
                   "constant in tracker.py.\n\n"
                   "Restart to load any other changes.").format(new_ver)
        else:
            headline = f"✅ Updated from v{old_ver} to v{new_ver}."
            sub = "Restart the app to load the new version."

        ttk.Label(body, text=headline,
                  font=("Segoe UI Semibold", 12)).pack(anchor=W)
        ttk.Label(body, text=sub, style="Muted.TLabel",
                  wraplength=380, justify=LEFT).pack(anchor=W, pady=(8, 16))

        btns = ttk.Frame(body)
        btns.pack(fill=X)
        ttk.Button(btns, text="Later",
                   command=dlg.destroy).pack(side=RIGHT)
        ttk.Button(btns, text="🔄 Restart Now", style="Primary.TButton",
                   command=lambda: restart_app(self.root)).pack(side=RIGHT, padx=(0, 8))

        dlg.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dlg.winfo_height()) // 3
        dlg.geometry(f"+{max(0,x)}+{max(0,y)}")

    def check_reminders(self):
        now = datetime.now()
        due = []
        for it in self.items:
            if it.get("reminder_dismissed"):
                continue
            d = parse_date(it.get("reminder_date"))
            if not d:
                continue
            t_str = it.get("reminder_time") or "09:00"
            try:
                t = datetime.strptime(t_str, "%H:%M").time()
            except ValueError:
                continue
            if datetime.combine(d, t) <= now:
                due.append(it)
        if due:
            names = "\n".join(f"• {i.get('company')} — {i.get('role','')}" for i in due)
            messagebox.showinfo("🔔 Reminders due", names)
            for it in due:
                it["reminder_dismissed"] = True
            save_data(self.items)


def main():
    root = Tk()
    TrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
