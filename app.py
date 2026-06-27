import streamlit as st
import gemini_agent
import task_manager
from datetime import date

# ── MUST be first Streamlit call ─────────────────────────────
st.set_page_config(
    page_title="Last-Minute Life Saver",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
section[data-testid="stSidebar"] { background: #0E0E10 !important; }
section[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif; }
.main { background: #111114; }
div[data-testid="stChatMessage"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── Demo seed ─────────────────────────────────────────────────
def seed_demo_tasks():
    if not task_manager.get_all_tasks():
        task_manager.add_task("Hackathon final submission",   "2026-06-29", "high",   "project")
        task_manager.add_task("Deploy app to Streamlit",     "2026-06-28", "high",   "project")
        task_manager.add_task("Write Google Doc description", "2026-06-28", "medium", "project")
        task_manager.add_task("Amazon ML Summer School prep", "2026-06-30", "high",   "academic")
        task_manager.add_task("Fill a form", "2026-06-30", "low",   "academic")
        task_manager.add_dependency(2, 1)
        task_manager.add_dependency(3, 2)

seed_demo_tasks()

# ── Helpers ───────────────────────────────────────────────────
def priority_color(p):
    return {"high": "#FF4B4B", "medium": "#FFAA00", "low": "#21C55D"}.get(p, "#555")

def badge(text, color, bg):
    return (f'<span style="font-size:10px;font-weight:600;padding:1px 7px;'
            f'border-radius:99px;background:{bg};color:{color};">{text}</span>')

def task_card(task):
    tid      = task.get("id", "?")
    priority = task.get("priority", "medium")
    done     = task.get("done", False)
    category = task.get("category", "general").upper()
    title    = task.get("title", "")
    deadline = task.get("deadline", "")
    color    = "#333" if done else priority_color(priority)

    try:
        diff = (date.fromisoformat(deadline) - date.today()).days
        if done:
            timing = '<span style="color:#555;">Completed</span>'
        elif diff < 0:
            timing = f'<span style="color:#FF4B4B;font-weight:600;">{abs(diff)}d overdue</span>'
        elif diff == 0:
            timing = '<span style="color:#FFAA00;font-weight:600;">Due today!</span>'
        elif diff == 1:
            timing = '<span style="color:#FFAA00;">Tomorrow</span>'
        else:
            timing = f'<span style="color:#888;">{diff}d left</span>'
    except Exception:
        timing = f'<span style="color:#888;">{deadline}</span>'

    title_style = "text-decoration:line-through;color:#444;" if done else "color:#F0F0F0;"
    card_bg     = "rgba(255,255,255,0.02)" if done else "rgba(255,255,255,0.05)"

    if done:
        b = badge("done", "#555", "#1A1A1A")
    elif priority == "high":
        b = badge("HIGH", "#FF6B6B", "#3D1111")
    elif priority == "medium":
        b = badge("MED", "#FFAA00", "#2D2000")
    else:
        b = badge("LOW", "#21C55D", "#0D2B1A")

    return f"""
<div style="border-left:3px solid {color};background:{card_bg};
            border-radius:6px;padding:9px 13px;margin:4px 0;">
  <div style="font-size:10px;color:#555;font-weight:700;
              letter-spacing:.06em;margin-bottom:3px;">
    #{tid} &nbsp;·&nbsp; {category}
  </div>
  <div style="font-size:14px;font-weight:500;margin:2px 0 5px;{title_style}">
    {title}
  </div>
  <div style="font-size:11px;display:flex;align-items:center;gap:8px;">
    <span style="color:#666;">📅 {deadline}</span>
    {timing}
    {b}
  </div>
</div>"""


# ════════════════════════════════════════════════════════════
# SIDEBAR — only UI rendering here, nothing else
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<p style="font-size:18px;font-weight:700;color:#F0F0F0;'
        'margin:0 0 16px;">📊 Urgency Dashboard</p>',
        unsafe_allow_html=True
    )

    analysis  = task_manager.get_urgency_analysis()
    all_tasks = task_manager.get_all_tasks()
    total     = len(all_tasks)
    done_n    = len(analysis["completed"])
    pct       = int(done_n / total * 100) if total else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total",   total)
    c2.metric("Pending", total - done_n)
    c3.metric("Done ✓",  done_n)

    if total:
        st.progress(pct / 100, text=f"{pct}% complete")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if analysis["overdue"]:
        st.markdown(
            '<div style="font-size:10px;font-weight:700;letter-spacing:.08em;'
            'text-transform:uppercase;color:#FF4B4B;border-bottom:0.5px solid #2A0A0A;'
            'padding-bottom:5px;margin:12px 0 6px;">🚨 Overdue</div>',
            unsafe_allow_html=True)
        for t in analysis["overdue"]:
            st.markdown(task_card(t), unsafe_allow_html=True)

    if analysis["due_today"]:
        st.markdown(
            '<div style="font-size:10px;font-weight:700;letter-spacing:.08em;'
            'text-transform:uppercase;color:#FFAA00;border-bottom:0.5px solid #2D2000;'
            'padding-bottom:5px;margin:12px 0 6px;">⏰ Due Today</div>',
            unsafe_allow_html=True)
        for t in analysis["due_today"]:
            st.markdown(task_card(t), unsafe_allow_html=True)

    if analysis["due_this_week"]:
        st.markdown(
            '<div style="font-size:10px;font-weight:700;letter-spacing:.08em;'
            'text-transform:uppercase;color:#4B9EFF;border-bottom:0.5px solid #0A1A2D;'
            'padding-bottom:5px;margin:12px 0 6px;">📅 This Week</div>',
            unsafe_allow_html=True)
        for t in analysis["due_this_week"]:
            st.markdown(task_card(t), unsafe_allow_html=True)

    if analysis["upcoming"]:
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        with st.expander(f"🔮 Upcoming ({len(analysis['upcoming'])})"):
            for t in analysis["upcoming"]:
                st.markdown(task_card(t), unsafe_allow_html=True)

    if analysis["completed"]:
        with st.expander(f"Completed  ·  {done_n} done"):
            for t in analysis["completed"]:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;'
                    f'padding:7px 10px;margin:3px 0;border-radius:5px;'
                    f'background:rgba(255,255,255,0.02);">'
                    f'<span style="font-size:13px;color:#21C55D;">✓</span>'
                    f'<span style="font-size:13px;color:#444;'
                    f'text-decoration:line-through;">{t["title"]}</span>'
                    f'<span style="font-size:11px;color:#333;margin-left:auto;">'
                    f'#{t["id"]} · {t.get("deadline","")}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    st.divider()

    if st.button("🧠 Procrastination Profile", use_container_width=True):
        profile = task_manager.get_procrastination_profile()
        if "message" in profile:
            st.info(profile["message"])
        else:
            avg     = profile.get("average_delay_days", 0)
            pattern = profile.get("pattern", "unknown")
            if pattern == "early":
                st.success(f"✨ You finish {abs(avg)} days early on average!")
            elif pattern == "late":
                st.warning(f"⚠️ You submit {avg} days late on average.")
            else:
                st.success("🎯 Right on time on average!")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("🔮 Pre-mortem Analysis", use_container_width=True):
        st.session_state.trigger = "premortem"
        st.rerun()

    if st.button("🚨 I'm Overwhelmed — Triage Me", use_container_width=True):
        st.session_state.trigger = "triage"
        st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    pending_tasks = [t for t in task_manager.get_all_tasks() if not t["done"]]
    if pending_tasks:
        ics = task_manager.generate_ics()
        st.download_button(
            label="📅 Export to Google Calendar",
            data=ics,
            file_name="my_tasks.ics",
            mime="text/calendar",
            use_container_width=True,
            help="Downloads .ics — import into Google Calendar, Apple Calendar, or Outlook"
        )
# ── Sidebar ends here ─────────────────────────────────────────


# ════════════════════════════════════════════════════════════
# MAIN AREA — everything below runs in the main content area
# ════════════════════════════════════════════════════════════

# Session state — initialised once, here, in the main area
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "briefing_done" not in st.session_state:
    st.session_state.briefing_done = False

# ── Morning briefing ─────────────────────────────────────────
def get_morning_briefing():
    tasks = task_manager.get_all_tasks()
    if not tasks or st.session_state.briefing_done:
        return
    analysis     = task_manager.get_urgency_analysis()
    urgent_count = len(analysis["overdue"]) + len(analysis["due_today"])
    if urgent_count == 0 and not analysis["due_this_week"]:
        return
    briefing_prompt = (
        f"Give me a quick morning briefing. I have {len(tasks)} tasks total. "
        f"{urgent_count} are overdue or due today. "
        f"{len(analysis['due_this_week'])} are due this week. "
        f"Use analyze_urgency and give me a 3-sentence priority plan for today."
    )
    with st.chat_message("assistant"):
        with st.spinner("Preparing your briefing..."):
            briefing = gemini_agent.run_agent(briefing_prompt, [])
        st.write(briefing)
    st.session_state.messages.append({"role": "assistant", "content": briefing})
    st.session_state.briefing_done = True

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <span style="font-size:36px;">⚡</span>
  <span style="font-size:28px;font-weight:700;color:#F0F0F0;">Last-Minute Life Saver</span>
</div>
<p style="color:#666;margin:0 0 24px;font-size:14px;">
  Describe your tasks in plain English — I'll parse, prioritize,
  and warn you about cascade effects.
</p>
""", unsafe_allow_html=True)

# ── Trigger handler — runs in main area, renders in chat ──────
trigger = st.session_state.pop("trigger", None)
if trigger == "premortem":
    auto_prompt = (
        "Run a pre-mortem analysis on all my pending tasks. "
        "What is most likely to go wrong with each one? "
        "Rank them by failure risk and give me one preventive action per task."
    )
elif trigger == "triage":
    auto_prompt = (
        "I'm completely overwhelmed. Use suggest_triage to analyse everything "
        "and give me a ruthless plan: exactly what to DO NOW, what to DEFER, "
        "and what to DROP entirely. Be specific — name the tasks."
    )
else:
    auto_prompt = None

if auto_prompt:
    with st.chat_message("user"):
        st.write(auto_prompt)
    st.session_state.messages.append({"role": "user", "content": auto_prompt})
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = gemini_agent.run_agent(auto_prompt, st.session_state.history)
        st.write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.history.append({"role": "user",      "content": auto_prompt})
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.rerun()

# ── Chat history ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Morning briefing (after history so it appears at bottom) ──
get_morning_briefing()

# ── Chat input ────────────────────────────────────────────────
prompt = st.chat_input(
    "e.g. 'Submit ML report by June 30 — depends on finishing research'"
)
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = gemini_agent.run_agent(prompt, st.session_state.history)
        st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.history.append({"role": "user",      "content": prompt})
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.rerun()