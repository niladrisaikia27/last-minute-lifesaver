# ⚡ Last-Minute Life Saver

> An AI-powered productivity companion that doesn't just remind you — it decides, prioritizes, and acts with you.

Built for the **Vibe2Ship Hackathon** (Coding Ninjas × Google for Developers) — Problem Statement 1: *The Last-Minute Life Saver*

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Gemini API](https://img.shields.io/badge/Gemini%20API-8E75B2?logo=google-gemini&logoColor=white)
![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)

---

## 🚀 Live Demo

🔗 **[Try it here](https://your-app-url.run.app)** — *(deployed on Google Cloud Run — replace with your actual link once deployed)*

---

## 📌 The Problem

Students, professionals, and entrepreneurs frequently miss deadlines, assignments, meetings, and important commitments. Existing productivity tools rely on passive reminders that are easy to ignore and do little to help users actually *complete* their tasks.

**Last-Minute Life Saver** moves beyond reminders. It reasons about your tasks, warns you about cascading consequences before they hit, decomposes vague goals into real plans, and tells you exactly what to drop when you're overwhelmed.

---

## ✨ Features

### 🤖 Agentic AI Core

Every action routes through a single Gemini-powered agent equipped with **14 callable tools** — not a chatbot bolted onto a to-do list, but a reasoning layer that decides which tool to use, when, and why.

| Feature | What it does |
|---|---|
| **Cascade Impact Detection** | Warns you when delaying one task will block others down the dependency chain |
| **Pre-mortem Analysis** | Reasons about what's *likely to go wrong* with each pending task before it happens — ranked by risk, with one preventive action each |
| **Triage Me** | When you're overwhelmed: a ruthless DO NOW / DEFER / DROP plan, naming real tasks by name |
| **Goal Decomposition** | State a big goal ("Crack Amazon ML Summer School") — Gemini researches the real deadline via web search, then breaks it into spaced, dependency-linked subtasks |
| **Smart Daily Schedule** | One click — an hour-by-hour plan for the *rest of today*, built from the current time and urgency, not a generic template |
| **Procrastination Profiler** | Learns your actual delay patterns from completed tasks — early, late, or on time, broken down by category |

### 🎙️ Multimodal Input

- **Voice** — speak a task naturally; Gemini transcribes it and routes it through the full agent, so a spoken task gets the same cascade/dependency reasoning as a typed one
- **Image to Tasks** — photograph a handwritten to-do list, whiteboard, or screenshot; Gemini reads it and adds every task it finds
- **Chat** — plain-English task entry, edits, and questions

### 📊 Analytics

- Completion rate by category
- Urgency distribution (overdue / due today / this week / upcoming)
- Delay patterns by category — visualizes the procrastination profile instead of just stating it

### 🛠️ Day-to-Day Usability

- Search and filter by title, priority, category, and status
- Manual edit/delete for any task
- Export pending tasks to Google/Apple/Outlook Calendar (`.ics`)
- Automatic morning briefing when urgent tasks exist
- Color-coded urgency dashboard (overdue, due today, this week, upcoming, completed)

---

## 🏗️ Architecture

```
last-minute-lifesaver/
├── app.py              # Streamlit UI — sidebar dashboard, chat, voice, image, analytics tabs
├── gemini_agent.py      # Gemini API integration — tool functions, agent runner, system prompt
├── task_manager.py      # Data layer — SQLite, pure functions, no Streamlit/Gemini dependencies
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── README.md
├── .gitignore
└── .env                 # GEMINI_API_KEY (local only — gitignored)
```

**Why this split:** `task_manager.py` knows nothing about Streamlit or Gemini — it's pure data logic. `gemini_agent.py` owns all model and tool-calling logic. `app.py` only renders. Each browser session gets its own isolated SQLite file in the system temp directory, so concurrent users never see or overwrite each other's tasks.

### How a request flows

1. User types, speaks, or uploads an image.
2. Voice and image inputs are transcribed/extracted first, then routed through the *same* agent pipeline as typed text — every input type gets the full reasoning, not a restricted shortcut.
3. Gemini decides which of its 14 tools to call — `add_task`, `analyze_urgency`, `get_cascade_impact`, `search_web_for_context`, `decompose_goal`, and more.
4. Tool results feed back to Gemini, which responds with the action taken, one proactive insight, and a specific next step.

---

## 🧰 Tech Stack

- **Frontend/Backend:** Streamlit (Python)
- **AI:** Gemini API (`gemini-3-flash-preview`) via the `google-genai` SDK — function calling, multimodal input (text/audio/image), and Google Search grounding
- **Prototyping:** Google AI Studio, used to test and refine prompts before integration
- **Database:** SQLite, isolated per session
- **Visualization:** Plotly + pandas
- **Deployment:** Docker → Google Cloud Run

---

## 🖥️ Running Locally

```bash
git clone https://github.com/niladrisaikia27/last-minute-lifesaver.git
cd last-minute-lifesaver
python -m venv venv
venv\Scripts\activate        # Windows — use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
```

```bash
streamlit run app.py
```

---

## ☁️ Deployment

Deployed as a containerized app on **Google Cloud Run**:

```bash
gcloud run deploy last-minute-lifesaver \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars GEMINI_API_KEY=your_key,GEMINI_MODEL=gemini-3-flash-preview
```

---

## 🎯 Hackathon Context

| | |
|---|---|
| **Hackathon** | Vibe2Ship (Coding Ninjas × Google for Developers) |
| **Problem Statement** | PS1 — The Last-Minute Life Saver |
| **Author** | Niladri Saikia — B.Tech CSE, NIT Silchar |
| **GitHub** | [@niladrisaikia27](https://github.com/niladrisaikia27) |

---

## 🔭 Future Improvements

- Real Google Calendar API (OAuth) push, replacing the static `.ics` export
- Multi-user accounts with persistent, non-temporary storage
- Deeper Google Workspace integration (Docs, Sheets) for richer goal context

---

## 🙏 Acknowledgments

Built for the Vibe2Ship Hackathon, organized by Coding Ninjas and Google for Developers.
