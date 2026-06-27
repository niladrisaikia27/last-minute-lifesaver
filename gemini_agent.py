from google import genai
from google.genai import types
import os, json
from dotenv import load_dotenv
from datetime import date
import task_manager

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

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

# --- Agent runner ---

SYSTEM_PROMPT = f"""You are a proactive productivity assistant called Life Saver.
Today is {date.today().isoformat()}.

When user mentions a task → use add_task immediately.
When asked what's pending → use analyze_urgency.
When a task might slip → use get_cascade_impact to warn them.
When tasks are related → use link_task_dependency.
When asked about patterns or habits → use get_procrastination_profile.
When a task is done → use mark_task_done.

Be proactive: if someone adds a task due very soon, warn them about
cascade effects. If they seem overwhelmed, suggest what to drop."""

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
                   link_task_dependency, get_procrastination_profile],
        )
    )
    return response.text