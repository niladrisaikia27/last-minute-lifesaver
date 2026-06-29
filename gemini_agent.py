from google import genai
from google.genai import types
import os, json
from dotenv import load_dotenv
from datetime import date, datetime
import task_manager
import streamlit as st  

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

import time, random

def _call_with_retry(fn, max_retries: int = 3, base_delay: float = 3.0):
    """Call fn() and retry on a 429 with exponential backoff + jitter.
    Converts a visible rate-limit wall into an invisible pause for most
    transient hits. Re-raises if retries run out, so the existing
    friendly error message still acts as a last-resort fallback."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            err = str(e)
            is_rate_limit = "429" in err or "RESOURCE_EXHAUSTED" in err
            if not is_rate_limit or attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 1))

def _db_path() -> str:
    """The current session's SQLite path, set by app.py's bootstrap
    block. Falls back to the shared default only if a tool is somehow
    called outside a normal Streamlit session."""
    return st.session_state.get("db_path", task_manager.DB_FILE)

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
    return (f"Saved as Task #{task['id']}: '{task['title']}' "
            f"due {task['deadline']} [{task['priority']}, {task['category']}]")

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

def build_daily_schedule() -> str:
    """Gather everything needed to build an hour-by-hour schedule for
    the REST of today: pending tasks, urgency breakdown, current time,
    and hours remaining until midnight — so the plan starts from now,
    not from midnight."""
    tasks = task_manager.get_all_tasks()
    pending = [t for t in tasks if not t["done"]]
    if not pending:
        return "No pending tasks — nothing to schedule."
    urgency = task_manager.get_urgency_analysis()
    now = datetime.now()
    hours_left = round((24 * 60 - (now.hour * 60 + now.minute)) / 60, 1)
    return json.dumps({
        "current_time": now.strftime("%H:%M"),
        "hours_until_midnight": hours_left,
        "pending_tasks": pending,
        "urgency_breakdown": urgency
    }, indent=2)

def search_web_for_context(query: str) -> str:
    """Search the web for relevant information — exam dates, competition
    deadlines, official announcements, or study resources.

    Args:
        query: What to search for, e.g. 'Amazon ML Summer School 2026 dates'
    """
    # Separate call with Google Search enabled — clean agentic delegation
    try:
        search_response = _call_with_retry(lambda: client.models.generate_content(
            model=MODEL,
            contents=f"Search and summarize: {query}. Be concise and factual.",
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        ))
        return search_response.text
    except Exception as e:
        return f"Search unavailable: {str(e)}"
    
def decompose_goal(goal: str) -> str:
    """Break a big, vague goal into concrete subtasks with realistic,
    spaced-out deadlines — in 1-2 Gemini calls total, not N."""
    today_str = date.today().isoformat()
    try:
        context = ""
        needs_research = any(kw in goal.lower() for kw in
            ["exam", "test", "competition", "hackathon", "summer school", "interview", "deadline"])
        if needs_research:
            search_resp = _call_with_retry(lambda: client.models.generate_content(
                model=MODEL,
                contents=f"Find the real, specific deadline for: {goal}. One or two sentences, concise.",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            ))
            context = search_resp.text

        prompt = (
            f"Today is {today_str}. Goal: \"{goal}\"\n"
            + (f"Research context: {context}\n" if context else "")
            + "Break this into 3-7 concrete subtasks with realistic, spaced-out "
              "deadlines, each at least 1 day apart, with buffer before any final "
              "deadline. Return ONLY valid JSON, no markdown fences:\n"
              '{"subtasks": [{"title": "...", "deadline": "YYYY-MM-DD", '
              '"priority": "high|medium|low", "category": "..."}], '
              '"summary": "2-3 sentences: count added, final deadline, encouragement"}'
        )
        result = _call_with_retry(lambda: client.models.generate_content(
            model=MODEL, contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        ))
        data = json.loads(result.text)

        added = []
        for sub in data.get("subtasks", []):
            t = task_manager.add_task(
                sub["title"], sub["deadline"], sub.get("priority", "medium"),
                sub.get("category", "general")
            )
            added.append(t)
        for i in range(1, len(added)):
            task_manager.add_dependency(added[i]["id"], added[i-1]["id"])

        return data.get("summary", f"Added {len(added)} subtasks toward: {goal}")
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return "Rate limit hit while decomposing the goal. Wait a moment and try again."
        return f"Could not decompose goal: {err[:200]}"

def edit_task(task_id: int, title: str = None, deadline: str = None,
              priority: str = None, category: str = None) -> str:
    """Edit an existing task — update its title, deadline, priority, or category.

    Args:
        task_id: The numeric ID of the task to edit
        title: New title (optional — leave None to keep current)
        deadline: New deadline in YYYY-MM-DD format (optional)
        priority: New priority — high, medium, or low (optional)
        category: New category (optional)
    """
    result = task_manager.update_task(task_id, title, deadline, priority, category)
    if not result:
        return f"Task {task_id} not found."
    return (f"Updated Task #{task_id}: '{result['title']}' "
            f"due {result['deadline']} [{result['priority']}]")

def delete_task(task_id: int) -> str:
    """Permanently delete a task.

    Args:
        task_id: The numeric ID of the task to delete
    """
    success = task_manager.delete_task(task_id)
    return f"Task #{task_id} deleted." if success else f"Task #{task_id} not found."

def extract_tasks_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Send an image to Gemini and extract all tasks from it using multimodal AI."""
    try:
        response = _call_with_retry(lambda: client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=f"""Today is {date.today().isoformat()}.
Look at this image carefully. It may be a handwritten to-do list, whiteboard,
screenshot, or any image containing tasks.

Extract EVERY task, deadline, and priority you can see.
For each task found:
- Call add_task with the task title
- Estimate deadline in YYYY-MM-DD format (if not shown, use today + 7 days)
- Set priority based on context clues (urgent words = high, etc.)
- Set category: academic, work, personal, or project

After adding all tasks, write a 2-line summary of what you extracted.""")
            ],
            config=types.GenerateContentConfig(
                tools=[add_task],
            )
        ))
        return response.text
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return "Rate limit hit. Wait 60 seconds and try again."
        return f"Could not process image: {err[:200]}"
    
def transcribe_audio(audio_bytes: bytes) -> tuple[str, str]:
    """Transcribe a short voice recording into plain text.

    Returns (transcript, error) — exactly one is non-empty. Deliberately
    does NOT call any task tools here; the transcript gets routed through
    run_agent afterwards so it benefits from the full Core Rules (cascade
    checks, triage, search, etc.) instead of a separate restricted path.
    """
    try:
        response = _call_with_retry(lambda: client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                types.Part.from_text(text=(
                    "Transcribe exactly what is said in this audio recording. "
                    "Return ONLY the transcribed words — no preamble, no "
                    "quotation marks, no commentary. If there is no audible "
                    "speech, return exactly: NO_SPEECH_DETECTED"
                ))
            ]
        ))
        text = (response.text or "").strip()
        if not text or text == "NO_SPEECH_DETECTED":
            return "", "Couldn't make out any speech in that recording — try again, speaking clearly in English."
        return text, ""
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return "", "Rate limit hit while transcribing. Wait a moment and try again."
        return "", f"Could not transcribe audio: {err[:200]}"

# --- Agent runner ---

def build_system_prompt() -> str:
    return f"""You are Life Saver, an advanced AI productivity companion.
Today is {date.today().isoformat()}.

## Core Rules — apply every single turn:
1. User mentions a task/deadline → call add_task FIRST, then analyze_urgency
2. Task added due within 3 days → also call get_cascade_impact immediately
3. User asks about an exam, competition, or deadline you're unsure about → call search_web_for_context first
4. User seems overwhelmed → call suggest_triage
5. Two tasks are related → call link_task_dependency
6. Task is done → call mark_task_done, then announce what's now unblocked
7. User wants to change a task → call edit_task
8. User wants to remove a task → call delete_task
9. Asked about patterns → call get_procrastination_profile
10. Asked to plan today or build a schedule → call build_daily_schedule (not analyze_urgency) and build an hour-by-hour timetable starting from the current time
11. User states a big, vague, or long-term goal instead of one concrete task (e.g. "crack X exam", "win Y hackathon", "get into Z", "learn [skill] by [event]") → call decompose_goal with their exact words. Do NOT call add_task yourself for a vague goal — let decompose_goal handle the breakdown.
12. Tool responses that include "Task #N" — reuse that exact ID for any later get_cascade_impact, link_task_dependency, edit_task, delete_task, or mark_task_done call in this same turn. Never guess an ID.

## What makes you different:
You search the web when you need real information.
You understand cascade effects — one delay breaks a chain.
You profile procrastination patterns to give personalized advice.
You help users decide what to drop, not just what to do.
You break vague goals into a concrete plan instead of one giant task.

## Response style:
- Lead with the action taken
- One proactive insight per response
- End with a specific next step
- Max 80 words unless analysis, a schedule, or a goal breakdown is requested
- Never say you lack access — use your tools"""

def run_agent(user_message: str, history: list = None) -> str:
    if history is None:
        history = []

    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )

    try:
        response = _call_with_retry(lambda: client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=build_system_prompt(),
                tools=[
                    add_task, get_all_tasks, mark_task_done,
                    analyze_urgency, get_cascade_impact,
                    link_task_dependency, get_procrastination_profile,
                    run_premortem_analysis, suggest_triage,
                    search_web_for_context, edit_task, delete_task,
                    build_daily_schedule, decompose_goal
                ],
            )
        ))
        return response.text

    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            # Extract retry seconds if available
            import re
            match = re.search(r'retry in (\d+)', err)
            wait = match.group(1) if match else "60"
            return (
                f"I'm thinking too fast — the API rate limit was hit. "
                f"Please wait {wait} seconds and try again. "
                f"This happens on the free tier (5 requests/minute). "
                f"Your tasks are safe and nothing was lost."
            )
        elif "404" in err or "not found" in err.lower():
            return "Model not found. Check your GEMINI_MODEL in .env file."
        else:
            return f"Something went wrong: {err[:200]}"