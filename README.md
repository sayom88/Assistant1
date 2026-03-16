# Harmony AI
### An Intelligent Life-Coordination Assistant for Women Professionals

> *Harmony AI unifies meal planning, grocery tracking, and work-life task management into a single conversational assistant — reducing the invisible mental load that women professionals carry every day.*

---

## What It Does

| Capability | Description |
|---|---|
|  **Smart Meal Planner** | Suggests weekly meals based on your dietary preferences, pantry stock, and calendar busyness. Quick meals on hectic days. |
| 🛒 **Predictive Grocery Tracker** | Tracks your pantry, learns what you have, and generates a precise shopping list — only what you actually need. |
| **Unified Task Board** | Manages work deadlines and home tasks together. Prioritises intelligently. Flags what's urgent. |
| **Calendar-Aware Intelligence** | Checks your upcoming schedule before making suggestions. Warns you about hectic days with no meal plan. |
| **Conversational Interface** | Just talk naturally. No complex navigation. Powered by GPT-4o with persistent memory across the conversation. |

---

## Setup (5 minutes)

### Prerequisites
- macOS 14.5
- Python 3.11
- An [OpenAI API key](https://platform.openai.com/api-keys) (requires GPT-4o access)

---

### Step 1 — Create a virtual environment

Open **Terminal** and run:

```bash
cd ~/Desktop          # or wherever you want the project
python3.11 -m venv harmony_env
source harmony_env/bin/activate
```

---

### Step 2 — Copy the project files

Copy the entire `harmony_ai/` folder to `~/Desktop/harmony_ai/` (or wherever you prefer).

---

### Step 3 — Install dependencies

```bash
cd harmony_ai
pip install -r requirements.txt
```

---

### Step 4 — Set your OpenAI API key

**Option A — .env file (recommended):**
```bash
cp .env.example .env
# Open .env in any text editor and replace the placeholder with your actual key
```

**Option B — Enter it in the app:**
You can also paste your API key directly in the sidebar when the app starts.

---

### Step 5 — Run Harmony AI

```bash
streamlit run app.py
```

Your browser will automatically open at `http://localhost:8501`.

---

## Project Structure

```
harmony_ai/
├── app.py              ← Streamlit UI (chat + sidebar dashboards)
├── assistant.py        ← OpenAI Assistants API (create, thread, run, poll)
├── tools.py            ← All function-calling tool schemas + dispatcher
├── data_store.py       ← JSON persistence (pantry, meals, tasks, calendar)
├── requirements.txt    ← Python dependencies
├── .env.example        ← API key template
├── README.md           ← This file
└── harmony_data/       ← Created automatically on first run
    ├── pantry.json
    ├── meal_plan.json
    ├── tasks.json
    ├── calendar.json
    ├── profile.json
    └── .assistant_id   ← Reuses same OpenAI Assistant across sessions
```

---

## Example Conversations

**Meal planning:**
> "Plan my meals for this week. I prefer Indian food and I'm vegetarian."

**Grocery:**
> "Generate my grocery list based on the meal plan."

**Pantry update:**
> "I just bought 2 kg of basmati rice, 500g of lentils, and a litre of milk."

**Tasks:**
> "Add a high-priority work task: Submit project proposal by Friday."

**Calendar-aware:**
> "Wednesday looks hectic. Suggest something quick for dinner that night."

**Overloaded day:**
> "I'm completely overwhelmed. What absolutely needs to get done today?"

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language Model | GPT-4o via OpenAI Assistants API |
| Persistent Threads | OpenAI Threads (context survives the session) |
| Function Calling | 14 tool functions across pantry, meals, tasks, calendar, profile |
| UI | Streamlit |
| Storage | Local JSON files (zero database setup) |
| Environment | Python 3.11 / macOS |

---

## Data & Privacy

All your data (pantry, tasks, meal plans) is stored **locally** in the `harmony_data/` folder on your machine. Nothing is sent to any server except your conversation messages to the OpenAI API (subject to OpenAI's privacy policy).

---

## Customisation

**Change the AI model:** In `assistant.py`, update `model="gpt-4o"` to `"gpt-4o-mini"` for lower cost.

**Add your own calendar events:** Edit `harmony_data/calendar.json` or ask Harmony to add them.

**Persist your profile:** Tell Harmony your name, dietary preferences, and household size — it saves everything automatically.

---

## Tips

- Harmony remembers the full conversation within a session via OpenAI Threads.
- Click **"New Conversation"** in the sidebar to start fresh (creates a new thread).
- The sidebar updates live as Harmony modifies your pantry, tasks, and meal plan.
- The same OpenAI Assistant is reused across runs (stored in `harmony_data/.assistant_id`).

---

