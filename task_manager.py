import sqlite3
from datetime import datetime, date

DB_FILE = "tasks.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            deadline     TEXT NOT NULL,
            priority     TEXT DEFAULT 'medium',
            category     TEXT DEFAULT 'general',
            done         INTEGER DEFAULT 0,
            created_at   TEXT,
            completed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dependencies (
            task_id    INTEGER,
            depends_on INTEGER,
            PRIMARY KEY (task_id, depends_on)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def _row(row, conn):
    d = dict(row)
    d["done"] = bool(d["done"])
    deps = conn.execute(
        "SELECT depends_on FROM dependencies WHERE task_id=?", (d["id"],)
    ).fetchall()
    d["dependencies"] = [r[0] for r in deps]
    return d

def get_all_tasks() -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks ORDER BY deadline ASC"
    ).fetchall()
    result = [_row(r, conn) for r in rows]
    conn.close()
    return result

def add_task(title: str, deadline: str,
             priority: str = "medium",
             category: str = "general") -> dict:
    conn = get_conn()
    # Deduplication — same title + not done = skip
    existing = conn.execute(
        "SELECT * FROM tasks WHERE LOWER(TRIM(title))=LOWER(TRIM(?)) AND done=0",
        (title,)
    ).fetchone()
    if existing:
        result = _row(existing, conn)
        conn.close()
        return result

    cur = conn.execute(
        """INSERT INTO tasks
           (title, deadline, priority, category, done, created_at, completed_at)
           VALUES (?,?,?,?,0,?,NULL)""",
        (title, deadline, priority, category, datetime.now().isoformat())
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)
    ).fetchone()
    result = _row(row, conn)
    conn.close()
    return result

def mark_done(task_id: int) -> bool:
    conn = get_conn()
    n = conn.execute(
        "UPDATE tasks SET done=1, completed_at=? WHERE id=?",
        (datetime.now().isoformat(), task_id)
    ).rowcount
    conn.commit()
    conn.close()
    return n > 0

def add_dependency(task_id: int, depends_on_id: int) -> bool:
    try:
        conn = get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO dependencies VALUES (?,?)",
            (task_id, depends_on_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_cascade_impact(task_id: int) -> list:
    conn = get_conn()
    all_tasks = get_all_tasks()
    affected = []

    def recurse(tid):
        rows = conn.execute(
            "SELECT task_id FROM dependencies WHERE depends_on=?", (tid,)
        ).fetchall()
        for r in rows:
            cid = r[0]
            if cid not in affected:
                affected.append(cid)
                recurse(cid)

    recurse(task_id)
    conn.close()
    return [t for t in all_tasks if t["id"] in affected]

def get_urgency_analysis() -> dict:
    tasks = get_all_tasks()
    today = date.today()
    overdue, due_today, this_week, upcoming, completed = [], [], [], [], []
    for t in tasks:
        if t["done"]:
            completed.append(t); continue
        try:
            days = (date.fromisoformat(t["deadline"]) - today).days
            if   days < 0:  t["days_overdue"] = abs(days); overdue.append(t)
            elif days == 0: due_today.append(t)
            elif days <= 7: t["days_left"] = days;         this_week.append(t)
            else:           t["days_left"] = days;         upcoming.append(t)
        except Exception:
            upcoming.append(t)
    return dict(overdue=overdue, due_today=due_today,
                due_this_week=this_week, upcoming=upcoming,
                completed=completed)

def get_procrastination_profile() -> dict:
    tasks = get_all_tasks()
    done  = [t for t in tasks if t.get("completed_at") and t.get("deadline")]
    if not done:
        return {"message": "No completed tasks yet. Finish some to see your delay pattern."}
    delays = []
    for t in done:
        try:
            dl   = date.fromisoformat(t["deadline"])
            comp = datetime.fromisoformat(t["completed_at"]).date()
            delays.append({
                "task":      t["title"],
                "delay_days": (comp - dl).days,
                "priority":  t["priority"],
                "category":  t.get("category", "general")
            })
        except Exception:
            pass
    if not delays:
        return {"message": "Could not calculate patterns."}
    avg      = sum(d["delay_days"] for d in delays) / len(delays)
    high     = [d for d in delays if d["priority"] == "high"]
    avg_high = sum(d["delay_days"] for d in high) / len(high) if high else None
    return {
        "total_completed":   len(delays),
        "average_delay_days": round(avg, 1),
        "high_priority_avg":  round(avg_high, 1) if avg_high is not None else None,
        "pattern": "early" if avg < 0 else "on-time" if avg == 0 else "late",
        "breakdown": delays
    }

def generate_ics() -> str:
    """Generate ICS calendar file from all pending tasks."""
    tasks = get_all_tasks()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Last-Minute Life Saver//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for task in tasks:
        if task.get("done"):
            continue
        try:
            deadline = task["deadline"].replace("-", "")
            lines += [
                "BEGIN:VEVENT",
                f"UID:task-{task['id']}@lastminute",
                f"SUMMARY:[{task['priority'].upper()}] {task['title']}",
                f"DTSTART;VALUE=DATE:{deadline}",
                f"DTEND;VALUE=DATE:{deadline}",
                f"DESCRIPTION:Category: {task.get('category','general')} | Priority: {task['priority']}",
                "STATUS:NEEDS-ACTION",
                "END:VEVENT",
            ]
        except Exception:
            pass
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)

def update_task(task_id: int, title: str = None, deadline: str = None,
                priority: str = None, category: str = None) -> dict:
    conn = get_conn()
    task = conn.execute(
        "SELECT * FROM tasks WHERE id=?", (task_id,)
    ).fetchone()
    if not task:
        conn.close()
        return {}
    conn.execute(
        "UPDATE tasks SET title=?, deadline=?, priority=?, category=? WHERE id=?",
        (title    or task["title"],
         deadline or task["deadline"],
         priority or task["priority"],
         category or task["category"],
         task_id)
    )
    conn.commit()
    updated = conn.execute(
        "SELECT * FROM tasks WHERE id=?", (task_id,)
    ).fetchone()
    result = _row(updated, conn)
    conn.close()
    return result

def delete_task(task_id: int) -> bool:
    conn = get_conn()
    n = conn.execute(
        "DELETE FROM tasks WHERE id=?", (task_id,)
    ).rowcount
    conn.execute(
        "DELETE FROM dependencies WHERE task_id=? OR depends_on=?",
        (task_id, task_id)
    )
    conn.commit()
    conn.close()
    return n > 0

def generate_ics() -> str:
    tasks = get_all_tasks()
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Last-Minute Life Saver//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for task in tasks:
        if task.get("done"):
            continue
        try:
            deadline = task["deadline"].replace("-", "")
            lines += [
                "BEGIN:VEVENT",
                f"UID:task-{task['id']}@lastminute",
                f"SUMMARY:[{task['priority'].upper()}] {task['title']}",
                f"DTSTART;VALUE=DATE:{deadline}",
                f"DTEND;VALUE=DATE:{deadline}",
                f"DESCRIPTION:Category: {task.get('category','general')} | Priority: {task['priority']}",
                "STATUS:NEEDS-ACTION",
                "END:VEVENT",
            ]
        except Exception:
            pass
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)