import streamlit as st
import gemini_agent
import task_manager

st.set_page_config(
    page_title="Last-Minute Life Saver",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Last-Minute Life Saver")
st.caption("Tell me your tasks in plain English. I'll organize and remind you.")

with st.sidebar:
    st.header("📋 Your Tasks")
    tasks = task_manager.get_all_tasks()
    if not tasks:
        st.info("No tasks yet. Start chatting!")
    for task in tasks:
        icon = "✅" if task["done"] else ("🔴" if task["priority"] == "high" else "🟡")
        st.markdown(
            f"{icon} **{task['title']}**  \n"
            f"`Due: {task['deadline']}` · `{task['priority']}`"
        )

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("e.g. 'Finish ML assignment by June 28, high priority'"):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = gemini_agent.run_agent(prompt)
        st.write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    st.rerun()