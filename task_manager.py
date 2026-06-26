import json, os
from datetime import datetime

TASKS_FILE = "tasks.json"

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def add_task(title: str, deadline: str, priority: str = "medium") -> dict:
    tasks = load_tasks()
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "deadline": deadline,
        "priority": priority,
        "done": False,
        "created_at": datetime.now().isoformat()
    }
    tasks.append(task)
    save_tasks(tasks)
    return task

def get_all_tasks() -> list:
    return load_tasks()

def mark_done(task_id: int) -> bool:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
            save_tasks(tasks)
            return True
    return False