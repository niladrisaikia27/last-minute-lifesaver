from google import genai
from google.genai import types
import os, json
from dotenv import load_dotenv
from datetime import date
import task_manager

# Try Streamlit secrets first (production), fall back to .env (local)
try:
    import streamlit as st
    API_KEY = st.secrets["GEMINI_API_KEY"]
    MODEL = st.secrets.get("GEMINI_MODEL", "gemini-3-flash-preview")
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.environ["GEMINI_API_KEY"]
    MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

client = genai.Client(api_key=API_KEY)

# --- Tool functions Gemini can call ---

def add_task(title: str, deadline: str,
             priority: str = "medium",
             category: str = "general") -> str:
    """Add a new task with deadline, priority, and category.

    Args:
        title: Task description
        deadline: Deadline in YYYY-MM-DD format
        priority: high, medium, or low
        category: Type e.g. academic, personal, work, project
    """
    task = task_manager.add_task(title, deadline, priority, category)
    return f"Saved: '{title}' due {deadline} [{priority}, {category}]"

def get_all_tasks() -> str:
    """Get all tasks the user has added so far."""
    tasks = task_manager.get_all_tasks()
    if not tasks:
        return "No tasks yet."
    return json.dumps(tasks, indent=2)

def mark_task_done(task_id: int) -> str:
    """Mark a task as completed.

    Args:
        task_id: The numeric ID of the task to mark done
    """
    success = task_manager.mark_done(task_id)
    return "Task marked done!" if success else "Task not found."

def analyze_urgency() -> str:
    """Analyze all tasks by urgency — overdue, due today, this week, upcoming."""
    result = task_manager.get_urgency_analysis()
    return json.dumps(result, indent=2)

def get_cascade_impact(task_id: int) -> str:
    """Find all tasks that will be affected if this task is delayed.

    Args:
        task_id: ID of the task to check
    """
    affected = task_manager.get_cascade_impact(task_id)
    if not affected:
        return f"Task {task_id} has no dependents. Safe to delay if needed."
    names = [t['title'] for t in affected]
    return (f"Warning: Delaying task {task_id} will cascade to "
            f"{len(affected)} other tasks: {', '.join(names)}")

def link_task_dependency(task_id: int, depends_on_task_id: int) -> str:
    """Link two tasks — task_id cannot start until depends_on_task_id is done.

    Args:
        task_id: The blocked task
        depends_on_task_id: The task that must finish first
    """
    success = task_manager.add_dependency(task_id, depends_on_task_id)
    return (f"Linked: Task {task_id} now depends on Task {depends_on_task_id}"
            if success else "Could not link tasks.")

def get_procrastination_profile() -> str:
    """Analyze the user's procrastination patterns from completed tasks."""
    profile = task_manager.get_procrastination_profile()
    return json.dumps(profile, indent=2)

def run_premortem_analysis() -> str:
    """Perform a pre-mortem analysis — reason through what could go wrong
    with each pending task BEFORE it happens. Rank tasks by failure risk,
    identify the most dangerous dependency chain, and suggest preventive actions."""
    tasks = task_manager.get_all_tasks()
    pending = [t for t in tasks if not t["done"]]
    if not pending:
        return "No pending tasks to analyze."
    urgency = task_manager.get_urgency_analysis()
    return json.dumps({
        "pending_tasks": pending,
        "urgency_breakdown": urgency
    }, indent=2)

def suggest_triage() -> str:
    """When user is overwhelmed, analyze all tasks and create a ruthless
    triage plan with three categories:
    - DO NOW: critical tasks that cannot be skipped
    - DEFER: tasks that can be pushed without major consequences
    - DROP: tasks to eliminate entirely to free up capacity"""
    tasks = task_manager.get_all_tasks()
    urgency = task_manager.get_urgency_analysis()
    return json.dumps({
        "all_tasks": tasks,
        "urgency": urgency
    }, indent=2)

# --- Agent runner ---

SYSTEM_PROMPT = f"""You are Life Saver, an advanced AI productivity companion.
Today is {date.today().isoformat()}. Deadline awareness is critical.

## Your Mission
You don't just store tasks. You actively reason about time, dependencies,
and human psychology to help users finish things before deadlines.

## Decision Rules — follow every turn:
1. Message contains a task/deadline → call add_task FIRST, then analyze_urgency
2. After adding any task due within 3 days → also call get_cascade_impact on it
3. User seems overwhelmed → call analyze_urgency, then recommend what to drop or defer
4. User mentions two related tasks → call link_task_dependency to connect them
5. Task marked done → call mark_task_done, then tell them what's now unblocked
6. Asked about habits/patterns → call get_procrastination_profile

## Response Style
- Lead with the action: "Added: [task] due [date] — [priority]"
- Follow with ONE proactive insight: urgency warning, cascade risk, or encouragement  
- End with a specific next step
- Stay under 80 words unless the user asks for detailed analysis
- Never say "I don't have access to your tasks" — use get_all_tasks

## What makes you different from a reminder app:
You understand that missing one task can break a chain of others.
You recognize when someone is overloaded and help them triage.
You remember the full conversation — use that context."""

def run_agent(user_message: str, history: list = None) -> str:
    if history is None:
        history = []

    # Build full conversation for Gemini
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[add_task, get_all_tasks, mark_task_done,
                   analyze_urgency, get_cascade_impact,
                   link_task_dependency, get_procrastination_profile,
                   run_premortem_analysis, suggest_triage],
        )
    )
    return response.text