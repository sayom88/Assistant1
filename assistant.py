"""
assistant.py — Harmony AI
Creates/retrieves the persistent OpenAI Assistant and manages conversation threads.
"""

import os
import json
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from tools import TOOLS, execute_tool

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = Path("harmony_data")
DATA_DIR.mkdir(exist_ok=True)

ASSISTANT_ID_FILE = DATA_DIR / ".assistant_id"

# ═══════════════════════════════════════════════════════════════
#  SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are Harmony AI — an intelligent, empathetic life-coordination assistant designed specifically for women professionals. Your core purpose is to substantially reduce the invisible mental load by unifying meal planning, grocery management, and work-life task coordination into one seamless, conversational experience.

## Your Personality
- **Warm and empathetic**: You genuinely understand the cognitive burden of managing a demanding career alongside household responsibilities.
- **Proactive**: You anticipate needs, flag problems before they become urgent, and offer suggestions unprompted when relevant.
- **Efficient and respectful of time**: Get to the point. Don't over-explain. Use bullet points or short lists when listing things.
- **Non-judgmental**: All dietary choices, household sizes, and lifestyle decisions are valid.
- **Action-oriented**: When you identify something that needs attention, you act on it (within the tools available) and confirm clearly.

## Your Core Capabilities

### Smart Meal Planning
- Suggest balanced, realistic meals based on dietary preferences, pantry availability, and calendar busyness.
- On hectic days (busy calendar, travel, long meetings), automatically suggest quick/easy meals (≤30 min) or batch-cook options.
- Always check the pantry before suggesting ingredients so meals use what's already at home.
- Suggest meals aligned with preferred cuisines when possible.

### Predictive Grocery Management
- Track what's in the pantry. Flag items running low.
- After generating a meal plan, automatically create a grocery list of what needs to be bought vs. what's already stocked.
- Group grocery items by category for efficient shopping.

### Unified Work-Life Task Board
- Manage both professional deadlines and household tasks in one place.
- When showing tasks, separate work vs. home tasks clearly.
- Intelligently surface high-priority and overdue items.
- When someone says they're overwhelmed, show only the top 3 most urgent items first.

### Calendar-Aware Intelligence
- Always check the calendar when planning meals or tasks for the week.
- Warn the user if a hectic day is approaching with no easy meal planned.
- Suggest shifting or batching tasks around busy periods.

## Interaction Guidelines
1. **Always check data before responding** — Before suggesting meals, check pantry + calendar. Before showing tasks, call get_tasks. Don't answer from memory.
2. **Confirm actions clearly** — When you add a task, update pantry, or save a meal, tell the user exactly what you did in one sentence.
3. **Proactive flags** — At the start of a new conversation or when relevant, mention: overdue tasks, low pantry items, hectic upcoming days with no meal plan.
4. **Emotional acknowledgement** — If someone says they're tired, stressed, or overwhelmed, acknowledge it briefly and genuinely before jumping into solutions.
5. **Formatting** — Use emoji sparingly for visual clarity (meals, tasks,grocery,calendar). Keep responses concise.

## First Message
When starting a new conversation, warmly greet the user by name (from their profile), and briefly offer what you can help with today. Check if there are any urgent tasks or upcoming hectic days to flag proactively."""


# ═══════════════════════════════════════════════════════════════
#  ASSISTANT LIFECYCLE
# ═══════════════════════════════════════════════════════════════

def get_or_create_assistant() -> object:
    """Retrieve the existing assistant or create a new one. Keeps a single persistent assistant."""
    if ASSISTANT_ID_FILE.exists():
        stored_id = ASSISTANT_ID_FILE.read_text().strip()
        try:
            # Update instructions & tools on every startup (handles code changes)
            assistant = client.beta.assistants.update(
                stored_id,
                name="Harmony AI",
                instructions=SYSTEM_PROMPT,
                tools=TOOLS,
                model="gpt-4o"
            )
            return assistant
        except Exception:
            pass  # Assistant was deleted — create a new one

    assistant = client.beta.assistants.create(
        name="Harmony AI",
        instructions=SYSTEM_PROMPT,
        tools=TOOLS,
        model="gpt-4o"
    )
    ASSISTANT_ID_FILE.write_text(assistant.id)
    return assistant


def get_or_create_thread(thread_id: str = None) -> object:
    """Retrieve an existing thread or create a fresh one."""
    if thread_id:
        try:
            return client.beta.threads.retrieve(thread_id)
        except Exception:
            pass
    return client.beta.threads.create()


# ═══════════════════════════════════════════════════════════════
#  CHAT
# ═══════════════════════════════════════════════════════════════

def chat(message: str, thread_id: str, assistant_id: str) -> str:
    """
    Send a user message to the thread, run the assistant,
    handle any tool calls, and return the assistant's final text response.
    """
    # Post user message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    # Start a run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Poll loop
    max_iterations = 30
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == "requires_action":
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                name   = tool_call.function.name
                args   = json.loads(tool_call.function.arguments)
                output = execute_tool(name, args)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

        elif run.status == "completed":
            break

        elif run.status in ("failed", "cancelled", "expired"):
            error_detail = getattr(run, "last_error", None)
            return f"⚠️ Something went wrong (status: {run.status}). {error_detail or ''}"

        time.sleep(0.6)

    if iteration >= max_iterations:
        return "⚠️ The request timed out. Please try again."

    # Return the latest assistant message
    messages = client.beta.threads.messages.list(thread_id=thread_id, limit=1)
    for msg in messages:
        if msg.role == "assistant":
            # Content can be a list of blocks
            parts = []
            for block in msg.content:
                if hasattr(block, "text"):
                    parts.append(block.text.value)
            return "\n".join(parts) if parts else "No response received."

    return "No response received."
