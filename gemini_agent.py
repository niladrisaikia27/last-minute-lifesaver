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

def add_task(title: str, deadline: str, priority: str = "medium") -> str:
    """Add a new task with a deadline and priority.

    Args:
        title: What the task is about
        deadline: Deadline date in YYYY-MM-DD format
        priority: Urgency level - high, medium, or low
    """
    task = task_manager.add_task(title, deadline, priority)
    return f"Saved: '{title}' due {deadline} [{priority} priority]"

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

# --- Agent runner ---

SYSTEM_PROMPT = f"""You are a proactive productivity assistant called Life Saver.
Today is {date.today().isoformat()}.
When the user mentions a task or deadline, immediately use add_task to save it.
When asked what's pending, use get_all_tasks.
When they say something is done, use mark_task_done.
Be concise, friendly, and action-oriented."""

def run_agent(user_message: str) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[add_task, get_all_tasks, mark_task_done],
        )
    )
    return response.text