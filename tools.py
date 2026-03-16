"""
tools.py — Harmony AI
Defines all OpenAI function-calling tool schemas and the execution dispatcher.
"""

import json
from data_store import (
    get_pantry, update_pantry_item,
    get_meal_plan, update_meal_plan, clear_meal_plan,
    get_tasks, add_task, complete_task, delete_task,
    get_profile, update_profile,
    get_calendar_events, add_calendar_event
)

# ═══════════════════════════════════════════════════════════════
#  TOOL DEFINITIONS  (passed to OpenAI Assistants API)
# ═══════════════════════════════════════════════════════════════

TOOLS = [
    # ── PANTRY ──────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_pantry_inventory",
            "description": "Retrieve the complete current pantry inventory — all items, quantities, units, and categories.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_pantry_item",
            "description": "Add, update quantity, or remove an item from the pantry. Set quantity to 0 to remove the item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":     {"type": "string", "description": "Item name (e.g., 'chicken breast', 'basmati rice')"},
                    "quantity": {"type": "number", "description": "Quantity available. Use 0 to remove item."},
                    "unit":     {"type": "string", "description": "Unit: kg, g, litre, ml, pieces, packets, cans, etc."},
                    "category": {"type": "string", "description": "Category: vegetables, fruits, dairy, grains, protein, spices, frozen, beverages, snacks, condiments"}
                },
                "required": ["name", "quantity"]
            }
        }
    },

    # ── MEAL PLAN ────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_meal_plan",
            "description": "Get the current weekly meal plan with all days and meal types planned so far.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_meal_plan",
            "description": "Set or update a specific meal in the meal plan. Always include key ingredients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "day":         {"type": "string", "description": "Day name: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"},
                    "meal_type":   {"type": "string", "description": "Meal type: breakfast, lunch, dinner, snack"},
                    "meal_name":   {"type": "string", "description": "Name of the dish (e.g., 'Dal Tadka with rice', 'Overnight oats')"},
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of main ingredients needed for this meal"
                    }
                },
                "required": ["day", "meal_type", "meal_name"]
            }
        }
    },

    # ── GROCERY ──────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "generate_grocery_list",
            "description": "Generate a smart shopping list based on the meal plan, subtracting items already in the pantry. Call this after the meal plan is set.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },

    # ── TASKS ────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_tasks",
            "description": "Retrieve tasks. Can filter by category and optionally include completed tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_category": {
                        "type": "string",
                        "description": "Filter by category: work, home, personal, or all (default: all)"
                    },
                    "show_completed": {
                        "type": "boolean",
                        "description": "Include completed tasks in the result (default: false)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new task to the unified work-life task board.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":    {"type": "string", "description": "Clear, actionable task description"},
                    "category": {"type": "string", "description": "Category: work, home, or personal"},
                    "priority": {"type": "string", "description": "Priority: high, medium, or low"},
                    "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format (optional)"},
                    "notes":    {"type": "string", "description": "Any extra context or notes (optional)"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed using its task_id. Always call get_tasks first to find the correct task_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The exact task_id string from get_tasks results"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Permanently delete a task by task_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The exact task_id string"}
                },
                "required": ["task_id"]
            }
        }
    },

    # ── CALENDAR ─────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Get upcoming calendar events. Use this to understand the user's schedule before suggesting meals or planning tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {"type": "integer", "description": "How many days ahead to look (default: 7)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": "Add a new event to the calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title":      {"type": "string", "description": "Event title"},
                    "date":       {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time":       {"type": "string", "description": "Time in HH:MM format or 'all-day'"},
                    "event_type": {"type": "string", "description": "work or personal"},
                    "busy":       {"type": "boolean", "description": "Is this a busy/hectic day (affects meal suggestions)?"}
                },
                "required": ["title", "date"]
            }
        }
    },

    # ── USER PROFILE ─────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Retrieve user profile: name, dietary preferences, restrictions, household size, preferred cuisines.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_profile",
            "description": "Update user profile settings like name, dietary preferences, allergies, or household size.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":                  {"type": "string"},
                    "dietary_preferences":   {"type": "array", "items": {"type": "string"}, "description": "e.g. vegetarian, vegan, high-protein"},
                    "dietary_restrictions":  {"type": "array", "items": {"type": "string"}, "description": "e.g. gluten-free, nut allergy, lactose intolerant"},
                    "household_size":        {"type": "integer", "description": "Number of people in the household"},
                    "preferred_cuisines":    {"type": "array", "items": {"type": "string"}, "description": "e.g. Indian, Mediterranean, Japanese"}
                },
                "required": []
            }
        }
    }
]


# ═══════════════════════════════════════════════════════════════
#  SMART GROCERY LIST GENERATOR
# ═══════════════════════════════════════════════════════════════

def _generate_grocery_list() -> dict:
    meal_plan = get_meal_plan()
    pantry    = get_pantry()

    if not meal_plan:
        return {"error": "No meal plan found. Please set up a meal plan first."}

    needed_raw = {}
    for day, meals in meal_plan.items():
        for meal_type, meal_info in meals.items():
            for ingredient in meal_info.get("ingredients", []):
                key = ingredient.strip().lower()
                needed_raw[key] = needed_raw.get(key, 0) + 1

    # Subtract pantry items
    to_buy   = [item for item in needed_raw if item not in pantry]
    in_stock = [item for item in needed_raw if item in pantry]

    return {
        "items_to_buy":        to_buy,
        "total_items_to_buy":  len(to_buy),
        "already_in_pantry":   in_stock,
        "pantry_coverage":     f"{len(in_stock)}/{len(needed_raw)} meal ingredients already stocked",
        "tip": "Add these to your preferred delivery app or shopping list."
    }


# ═══════════════════════════════════════════════════════════════
#  TOOL DISPATCHER
# ═══════════════════════════════════════════════════════════════

def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Route a tool call from the OpenAI assistant to the correct function."""
    try:
        if tool_name == "get_pantry_inventory":
            result = get_pantry()

        elif tool_name == "update_pantry_item":
            result = update_pantry_item(**tool_args)

        elif tool_name == "get_meal_plan":
            result = get_meal_plan()

        elif tool_name == "update_meal_plan":
            result = update_meal_plan(**tool_args)

        elif tool_name == "generate_grocery_list":
            result = _generate_grocery_list()

        elif tool_name == "get_tasks":
            tasks         = get_tasks()
            show_done     = tool_args.get("show_completed", False)
            filter_cat    = tool_args.get("filter_category", "all")
            result = {
                k: v for k, v in tasks.items()
                if (show_done or not v.get("completed", False))
                and (filter_cat == "all" or v.get("category") == filter_cat)
            }

        elif tool_name == "add_task":
            result = add_task(**tool_args)

        elif tool_name == "complete_task":
            result = complete_task(**tool_args)

        elif tool_name == "delete_task":
            result = delete_task(**tool_args)

        elif tool_name == "get_calendar_events":
            days   = tool_args.get("days_ahead", 7)
            result = get_calendar_events(days)

        elif tool_name == "add_calendar_event":
            result = add_calendar_event(**tool_args)

        elif tool_name == "get_user_profile":
            result = get_profile()

        elif tool_name == "update_user_profile":
            result = update_profile(tool_args)

        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return json.dumps(result, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)})
