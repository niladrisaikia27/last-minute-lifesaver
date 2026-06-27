import streamlit as st
import gemini_agent
import task_manager

st.set_page_config(
    page_title="Last-Minute Life Saver",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Last-Minute Life Saver")
st.caption("Tell me your tasks in plain English. I'll organize, warn, and keep you ahead.")

# Smart urgency dashboard sidebar
with st.sidebar:
    st.header("📊 Urgency Dashboard")
    analysis = task_manager.get_urgency_analysis()

    col1, col2 = st.columns(2)
    pending = (len(analysis["overdue"]) + len(analysis["due_today"])
               + len(analysis["due_this_week"]) + len(analysis["upcoming"]))
    col1.metric("Pending", pending)
    col2.metric("Done ✓", len(analysis["completed"]))

    if analysis["overdue"]:
        st.error(f"🚨 Overdue — {len(analysis['overdue'])} task(s)")
        for t in analysis["overdue"]:
            st.markdown(f"**{t['title']}** · {t.get('days_overdue',0)}d overdue")

    if analysis["due_today"]:
        st.warning(f"⏰ Due Today — {len(analysis['due_today'])} task(s)")
        for t in analysis["due_today"]:
            st.markdown(f"**{t['title']}** · `{t['priority']}`")

    if analysis["due_this_week"]:
        st.info(f"📅 This Week — {len(analysis['due_this_week'])} task(s)")
        for t in analysis["due_this_week"]:
            st.markdown(f"**{t['title']}** · {t.get('days_left','?')}d left")

    if analysis["upcoming"]:
        with st.expander(f"🔮 Upcoming ({len(analysis['upcoming'])})"):
            for t in analysis["upcoming"]:
                st.markdown(f"**{t['title']}** · due {t['deadline']}")

    if analysis["completed"]:
        with st.expander(f"✅ Completed ({len(analysis['completed'])})"):
            for t in analysis["completed"]:
                st.markdown(f"~~{t['title']}~~")

    st.divider()
    if st.button("🧠 My procrastination profile"):
        profile = task_manager.get_procrastination_profile()
        if "message" in profile:
            st.info(profile["message"])
        else:
            avg = profile.get("average_delay_days", 0)
            pattern = profile.get("pattern", "unknown")
            if pattern == "early":
                st.success(f"You finish {abs(avg)} days early on average. 🎉")
            elif pattern == "late":
                st.warning(f"You submit {avg} days late on average. Let's fix that.")
            else:
                st.success("You're right on time on average! Keep it up.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
prompt = st.chat_input(
    "e.g. 'I need to submit my report before the presentation on June 28'"
)
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = gemini_agent.run_agent(
                prompt, st.session_state.history
            )
        st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.history.append({"role": "user", "content": prompt})
    st.session_state.history.append({"role": "assistant", "content": reply})

    st.rerun()