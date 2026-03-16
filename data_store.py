"""
data_store.py — Harmony AI
Lightweight JSON-based persistence for pantry, meal plans, tasks, and user profile.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("harmony_data")
DATA_DIR.mkdir(exist_ok=True)


# ─────────────────────────── helpers ────────────────────────────

def _load(filename: str) -> dict:
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(filename: str, data: dict) -> None:
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ─────────────────────────── PANTRY ─────────────────────────────

def get_pantry() -> dict:
    return _load("pantry.json")


def update_pantry_item(name: str, quantity: float, unit: str = "units", category: str = "general") -> dict:
    pantry = get_pantry()
    key = name.strip().lower()
    if quantity <= 0:
        pantry.pop(key, None)
    else:
        pantry[key] = {
            "display_name": name.strip(),
            "quantity": quantity,
            "unit": unit,
            "category": category,
            "updated": datetime.now().isoformat()
        }
    _save("pantry.json", pantry)
    return pantry


# ─────────────────────────── MEAL PLAN ──────────────────────────

def get_meal_plan() -> dict:
    return _load("meal_plan.json")


def update_meal_plan(day: str, meal_type: str, meal_name: str, ingredients: list = None) -> dict:
    plan = get_meal_plan()
    if day not in plan:
        plan[day] = {}
    plan[day][meal_type] = {
        "name": meal_name,
        "ingredients": ingredients or [],
        "updated": datetime.now().isoformat()
    }
    _save("meal_plan.json", plan)
    return plan


def clear_meal_plan() -> dict:
    _save("meal_plan.json", {})
    return {}


# ─────────────────────────── TASKS ──────────────────────────────

def get_tasks() -> dict:
    return _load("tasks.json")


def add_task(title: str, category: str = "personal", priority: str = "medium",
             due_date: str = None, notes: str = "") -> dict:
    tasks = get_tasks()
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')[:19]}"
    tasks[task_id] = {
        "title": title,
        "category": category,      # work | home | personal
        "priority": priority,      # high | medium | low
        "due_date": due_date,
        "notes": notes,
        "completed": False,
        "created": datetime.now().isoformat()
    }
    _save("tasks.json", tasks)
    return tasks


def complete_task(task_id: str) -> dict:
    tasks = get_tasks()
    if task_id in tasks:
        tasks[task_id]["completed"] = True
        tasks[task_id]["completed_at"] = datetime.now().isoformat()
        _save("tasks.json", tasks)
    return tasks


def delete_task(task_id: str) -> dict:
    tasks = get_tasks()
    tasks.pop(task_id, None)
    _save("tasks.json", tasks)
    return tasks


# ─────────────────────────── USER PROFILE ───────────────────────

def get_profile() -> dict:
    defaults = {
        "name": "User",
        "dietary_preferences": [],
        "dietary_restrictions": [],
        "household_size": 2,
        "preferred_cuisines": []
    }
    stored = _load("profile.json")
    return {**defaults, **stored}


def update_profile(updates: dict) -> dict:
    profile = get_profile()
    profile.update(updates)
    _save("profile.json", profile)
    return profile


# ─────────────────────────── CALENDAR (simulated) ───────────────

def get_calendar_events(days_ahead: int = 7) -> dict:
    stored = _load("calendar.json")
    if stored.get("events"):
        return stored

    # Default sample events so the assistant has something to reason about
    today = datetime.now()
    events = [
        {
            "title": "Team standup",
            "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "09:00",
            "type": "work",
            "busy": False
        },
        {
            "title": "Client presentation — Q2 Review",
            "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "time": "14:00",
            "type": "work",
            "busy": True
        },
        {
            "title": "Doctor appointment",
            "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "time": "11:00",
            "type": "personal",
            "busy": False
        },
        {
            "title": "All-day offsite / travel",
            "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "time": "all-day",
            "type": "work",
            "busy": True
        }
    ]
    result = {"events": events}
    _save("calendar.json", result)
    return result


def add_calendar_event(title: str, date: str, time: str = "", event_type: str = "personal", busy: bool = False) -> dict:
    cal = get_calendar_events()
    cal.setdefault("events", []).append({
        "title": title,
        "date": date,
        "time": time,
        "type": event_type,
        "busy": busy
    })
    _save("calendar.json", cal)
    return cal
