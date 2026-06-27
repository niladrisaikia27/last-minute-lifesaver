import json, os
from datetime import datetime, date

TASKS_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(title: str, deadline: str,
             priority: str = "medium",
             category: str = "general") -> dict:
    tasks = load_tasks()
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "deadline": deadline,
        "priority": priority,
        "category": category,
        "done": False,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "dependencies": []
    }
    tasks.append(task)
    save_tasks(tasks)
    return task

def get_all_tasks():
    return load_tasks()

def mark_done(task_id: int) -> bool:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            t["completed_at"] = datetime.now().isoformat()
            save_tasks(tasks)
            return True
    return False

def add_dependency(task_id: int, depends_on_id: int) -> bool:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t.setdefault("dependencies", [])
            if depends_on_id not in t["dependencies"]:
                t["dependencies"].append(depends_on_id)
            save_tasks(tasks)
            return True
    return False

def get_cascade_impact(task_id: int) -> list:
    """Find all tasks blocked if this task is delayed."""
    tasks = load_tasks()
    affected_ids = []

    def find_dependents(tid):
        for t in tasks:
            if tid in t.get("dependencies", []):
                if t["id"] not in affected_ids:
                    affected_ids.append(t["id"])
                    find_dependents(t["id"])

    find_dependents(task_id)
    return [t for t in tasks if t["id"] in affected_ids]

def get_urgency_analysis() -> dict:
    tasks = load_tasks()
    today = date.today()
    overdue, due_today, this_week, upcoming, completed = [], [], [], [], []

    for t in tasks:
        if t["done"]:
            completed.append(t)
            continue
        try:
            dl = date.fromisoformat(t["deadline"])
            days = (dl - today).days
            if days < 0:
                t["days_overdue"] = abs(days)
                overdue.append(t)
            elif days == 0:
                due_today.append(t)
            elif days <= 7:
                t["days_left"] = days
                this_week.append(t)
            else:
                t["days_left"] = days
                upcoming.append(t)
        except:
            upcoming.append(t)

    return {
        "overdue": overdue, "due_today": due_today,
        "due_this_week": this_week, "upcoming": upcoming,
        "completed": completed
    }

def get_procrastination_profile() -> dict:
    tasks = load_tasks()
    done = [t for t in tasks if t.get("completed_at") and t.get("deadline")]
    if not done:
        return {"message": "No completed tasks yet. Finish some tasks to see your pattern."}

    delays = []
    for t in done:
        try:
            dl = date.fromisoformat(t["deadline"])
            comp = datetime.fromisoformat(t["completed_at"]).date()
            delays.append({
                "task": t["title"],
                "delay_days": (comp - dl).days,
                "priority": t["priority"],
                "category": t.get("category", "general")
            })
        except:
            pass

    if not delays:
        return {"message": "Could not calculate patterns."}

    avg = sum(d["delay_days"] for d in delays) / len(delays)
    high = [d for d in delays if d["priority"] == "high"]
    avg_high = sum(d["delay_days"] for d in high) / len(high) if high else None

    return {
        "total_completed": len(delays),
        "average_delay_days": round(avg, 1),
        "average_high_priority_delay": round(avg_high, 1) if avg_high else None,
        "pattern": "early" if avg < 0 else "on-time" if avg == 0 else "late",
        "breakdown": delays
    }