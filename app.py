"""
app.py — Harmony AI
Streamlit-based conversational UI with live sidebar dashboards.
"""

import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────── Page Config ────────────────────────
st.set_page_config(
    page_title="Harmony AI",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────── Custom CSS ─────────────────────────
st.markdown("""
<style>
/* General */
body { font-family: 'Inter', sans-serif; }

/* Header */
.harmony-header {
    background: linear-gradient(135deg, #6B48FF 0%, #C77DFF 100%);
    color: white;
    padding: 1.2rem 1.8rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 12px;
}
.harmony-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
.harmony-header p  { margin: 0; font-size: 0.9rem; opacity: 0.9; }

/* Chat messages */
.user-msg {
    background: #EDE7FF;
    border-radius: 16px 16px 4px 16px;
    padding: 0.75rem 1rem;
    margin: 0.4rem 0;
    text-align: right;
    color: #2D1B69;
    font-size: 0.95rem;
}
.ai-msg {
    background: #F8F5FF;
    border: 1px solid #E2D9FF;
    border-radius: 16px 16px 16px 4px;
    padding: 0.75rem 1rem;
    margin: 0.4rem 0;
    color: #1A1A2E;
    font-size: 0.95rem;
}

/* Sidebar cards */
.sidebar-card {
    background: #FAFAFA;
    border: 1px solid #E8E8E8;
    border-radius: 12px;
    padding: 0.8rem;
    margin-bottom: 0.8rem;
}
.sidebar-card h4 { margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #6B48FF; font-weight: 600; }

/* Status pills */
.pill-high   { background: #FFE4E4; color: #D32F2F; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; }
.pill-medium { background: #FFF3E0; color: #E65100; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; }
.pill-low    { background: #E8F5E9; color: #2E7D32; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; }

/* Suggested prompts */
.prompt-btn {
    background: #F0EBFF;
    border: 1px solid #C9B8FF;
    border-radius: 20px;
    padding: 0.4rem 0.9rem;
    margin: 0.2rem;
    cursor: pointer;
    font-size: 0.85rem;
    color: #6B48FF;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────── Session State ──────────────────────
def init_state():
    defaults = {
        "thread_id":    None,
        "assistant_id": None,
        "messages":     [],          # [{role, content}]
        "initialized":  False,
        "api_key_set":  bool(os.getenv("OPENAI_API_KEY")),
        "loading":      False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────── Data helpers ───────────────────────
def load_data(filename, default=None):
    path = Path("harmony_data") / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default or {}

def get_pending_tasks():
    tasks = load_data("tasks.json")
    return {k: v for k, v in tasks.items() if not v.get("completed")}

def get_pantry():
    return load_data("pantry.json")

def get_meal_plan():
    return load_data("meal_plan.json")

def get_calendar():
    return load_data("calendar.json", {"events": []})

def get_profile():
    return load_data("profile.json", {"name": "there"})


# ─────────────────────────── Initialise Assistant ───────────────
def initialise_harmony():
    with st.spinner("🌸 Starting Harmony AI…"):
        from assistant import get_or_create_assistant, get_or_create_thread, chat
        assistant = get_or_create_assistant()
        thread    = get_or_create_thread()
        st.session_state.assistant_id = assistant.id
        st.session_state.thread_id    = thread.id
        st.session_state.initialized  = True
        # Welcome message
        welcome = chat("Hello! Please greet me, check my profile, upcoming calendar, and any pending tasks, then give me a brief friendly status update.", thread.id, assistant.id)
        st.session_state.messages.append({"role": "assistant", "content": welcome})


# ─────────────────────────── Sidebar ────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🌸 Harmony AI")
        st.markdown("---")

        # ── API Key entry if missing ─────────────────────────────
        if not st.session_state.api_key_set:
            st.warning("OpenAI API key not set")
            api_key = st.text_input("Enter your OpenAI API key:", type="password", key="api_key_input")
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
                # Patch the openai client in assistant module
                import assistant as a_module
                from openai import OpenAI
                a_module.client = OpenAI(api_key=api_key)
                st.session_state.api_key_set = True
                st.rerun()
            st.stop()

        # ── Task Summary ─────────────────────────────────────────
        st.markdown("### ✅ Tasks")
        tasks = get_pending_tasks()
        if tasks:
            work_tasks = [(k, v) for k, v in tasks.items() if v.get("category") == "work"]
            home_tasks = [(k, v) for k, v in tasks.items() if v.get("category") != "work"]
            if work_tasks:
                st.markdown("**💼 Work**")
                for _, t in work_tasks[:3]:
                    priority = t.get("priority", "medium")
                    colour   = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                    due      = f" · {t['due_date']}" if t.get("due_date") else ""
                    st.markdown(f"{colour} {t['title']}{due}")
            if home_tasks:
                st.markdown("**🏠 Home**")
                for _, t in home_tasks[:3]:
                    priority = t.get("priority", "medium")
                    colour   = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                    st.markdown(f"{colour} {t['title']}")
            if len(tasks) > 6:
                st.caption(f"…and {len(tasks)-6} more. Ask Harmony to show all.")
        else:
            st.caption("No pending tasks. Ask Harmony to add some!")

        st.markdown("---")

        # ── Pantry Summary ───────────────────────────────────────
        st.markdown("### 🛒 Pantry")
        pantry = get_pantry()
        if pantry:
            by_cat = {}
            for item, info in pantry.items():
                cat = info.get("category", "other")
                by_cat.setdefault(cat, []).append(
                    f"{info.get('display_name', item)} ({info['quantity']} {info.get('unit','')})"
                )
            for cat, items in list(by_cat.items())[:3]:
                st.markdown(f"**{cat.title()}**")
                for i in items[:2]:
                    st.caption(f"• {i}")
            total = len(pantry)
            st.caption(f"{total} item{'s' if total != 1 else ''} tracked")
        else:
            st.caption("Pantry is empty. Tell Harmony what you have!")

        st.markdown("---")

        # ── Meal Plan Summary ────────────────────────────────────
        st.markdown("### 🥗 This Week's Meals")
        plan = get_meal_plan()
        if plan:
            days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            for day in days_order:
                if day in plan:
                    meals = plan[day]
                    meal_str = " · ".join(v["name"] for v in meals.values())
                    st.markdown(f"**{day[:3]}** — {meal_str}")
        else:
            st.caption("No meal plan yet. Ask Harmony to plan your week!")

        st.markdown("---")

        # ── Calendar ─────────────────────────────────────────────
        st.markdown("### 📅 Coming Up")
        cal = get_calendar()
        events = cal.get("events", [])[:4]
        if events:
            for e in events:
                busy_tag = " 🔥" if e.get("busy") else ""
                st.caption(f"**{e['date']}** {e.get('time','')}  \n{e['title']}{busy_tag}")
        else:
            st.caption("No upcoming events.")

        st.markdown("---")

        # ── Reset button ─────────────────────────────────────────
        if st.button("🔄 New Conversation", use_container_width=True):
            from assistant import get_or_create_thread
            thread = get_or_create_thread()
            st.session_state.thread_id = thread.id
            st.session_state.messages  = []
            st.rerun()

        st.caption("Powered by OpenAI Assistants API · gpt-4o")


# ─────────────────────────── Main Chat UI ───────────────────────
def render_chat():
    # Header
    profile = get_profile()
    name    = profile.get("name", "there")
    st.markdown(f"""
    <div class="harmony-header">
        <div>
            <h1>🌸 Harmony AI</h1>
            <p>Your intelligent life-coordination assistant, {name}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Init on first load
    if not st.session_state.initialized:
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("### Welcome to Harmony AI 🌸")
            st.markdown(
                "I'm your personal life-coordination assistant. I help you manage "
                "meal planning, grocery tracking, and your work-life task board — all in one conversation."
            )
            st.markdown("**To get started, I need your OpenAI API key.**")
            if not st.session_state.api_key_set:
                st.info("Please enter your API key in the sidebar →")
            else:
                if st.button("✨ Start Harmony AI", use_container_width=True, type="primary"):
                    initialise_harmony()
                    st.rerun()
        return

    # ── Chat history ──────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                # Render assistant message with proper markdown
                with st.chat_message("assistant", avatar="🌸"):
                    st.markdown(msg["content"])

    # ── Suggested prompts (only when conversation is short) ───────
    if len(st.session_state.messages) <= 2:
        st.markdown("**Quick start — try asking:**")
        suggestions = [
            "Plan my meals for this week 🥗",
            "What tasks are due this week? ✅",
            "What's in my pantry? 🛒",
            "I'm exhausted — what do I need to do today?",
            "Generate my grocery list 📝",
            "Add a task: Book car service, high priority",
        ]
        cols = st.columns(3)
        for i, s in enumerate(suggestions):
            if cols[i % 3].button(s, key=f"sug_{i}", use_container_width=True):
                send_message(s)

    # ── Input ─────────────────────────────────────────────────────
    st.markdown("---")
    col_input, col_btn = st.columns([8, 1])
    with col_input:
        user_input = st.chat_input("Ask Harmony anything…")
    
    if user_input:
        send_message(user_input)


def send_message(text: str):
    from assistant import chat as harmony_chat

    st.session_state.messages.append({"role": "user", "content": text})

    with st.spinner("🌸 Thinking…"):
        response = harmony_chat(
            text,
            st.session_state.thread_id,
            st.session_state.assistant_id
        )

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()


# ─────────────────────────── Entry Point ────────────────────────
render_sidebar()
render_chat()
