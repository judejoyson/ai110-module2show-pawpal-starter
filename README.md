# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧱 Implementation Summary

The core logic lives in `pawpal_system.py`, split into data classes that hold state and one logic class that makes decisions:

- **`Task`** — a single care activity: title, duration in minutes, priority ("low"/"medium"/"high"), frequency, and completion status. It converts its priority to a sortable number via `priority_score()`.
- **`Pet`** — a pet's basic info plus its own list of tasks (`add_task`, `remove_task`, `get_tasks`).
- **`Owner`** — holds the time budget (`available_minutes`) and all pets. Its key method is `get_all_tasks()`, which returns every pet's tasks as `(pet, task)` pairs so tasks stay attributed to their pet.
- **`Scheduler`** — the "brain." `build_schedule()` reads `Owner.get_all_tasks()` (never a single pet), drops completed tasks, sorts the rest by priority (shorter tasks win ties), and greedily fills the owner's time budget, assigning each task a start/end time from `start_hour` onward.
- **`Schedule` / `ScheduledTask`** — the output: an ordered list of time-stamped entries, each carrying a `reason` string. `explain()` produces a human-readable justification and `to_display_rows()` formats rows for the Streamlit table.

How they work together: the UI (or `main.py`) builds an `Owner` with `Pet`s and `Task`s, hands the owner to a `Scheduler`, and gets back a `Schedule` ready to display — so the scheduling algorithm can change without touching the data classes or the UI.

`main.py` is a terminal demo of this flow, and `tests/test_pawpal.py` covers the core task behaviors.

## 🖥️ Sample Output

Terminal output from running `python main.py` (two pets sharing one 90-minute budget, showing sorting, filtering, recurrence, and conflict detection):

```
All tasks in the order they were added:
  18:00    Evening walk          30 min  high    [pending]
  07:30    Morning walk          30 min  high    [pending]
  anytime  Brush coat            15 min  low     [pending]
  15:30    Play session          25 min  medium  [pending]
  08:00    Give meds             10 min  high    [pending]
  07:45    Breakfast             15 min  high    [pending]
  09:00    Clean litter box      10 min  medium  [done]

Sorted by time (sort_by_time):
  07:30    Morning walk          30 min  high    [pending]
  07:45    Breakfast             15 min  high    [pending]
  08:00    Give meds             10 min  high    [pending]
  09:00    Clean litter box      10 min  medium  [done]
  15:30    Play session          25 min  medium  [pending]
  18:00    Evening walk          30 min  high    [pending]
  anytime  Brush coat            15 min  low     [pending]

Filtered: Luna's tasks only:
  15:30    Play session          25 min  medium  [pending]
  08:00    Give meds             10 min  high    [pending]
  07:45    Breakfast             15 min  high    [pending]
  09:00    Clean litter box      10 min  medium  [done]

Marking Luna's daily 'Give meds' complete...
  Auto-created next occurrence: due 2026-10-20 (daily)

Today's Schedule for Jordan (2026-10-19)
Budget: 90 min | Scheduled: 90 min
------------------------------------------------------------------------
Time          Pet     Task                  Min  Priority
------------------------------------------------------------------------
08:00-08:15   Luna    Breakfast              15  high
08:15-08:45   Mochi   Evening walk           30  high
08:45-09:15   Mochi   Morning walk           30  high
09:15-09:30   Mochi   Brush coat             15  low
------------------------------------------------------------------------
Skipped (not enough time): Play session

WARNING - preferred-time conflicts detected:
  ! 'Morning walk' (Mochi, 07:30-08:00) overlaps 'Breakfast' (Luna, 07:45-08:00)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\joyso\ai110-module2show-pawpal-starter
collected 2 items

tests\test_pawpal.py ..                                                  [100%]

============================== 2 passed in 0.04s ==============================
```

## 📐 Smarter Scheduling

Four logic upgrades beyond the basic greedy scheduler, each with the method that implements it:

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | `Scheduler.sort_by_time()`, `Scheduler._sort_tasks()` | `sort_by_time` orders tasks by their `"HH:MM"` preferred time using a `lambda` key (zero-padded strings sort chronologically; untimed tasks sort last via a `"99:99"` sentinel). `_sort_tasks` orders the actual plan by priority, shorter duration breaking ties. |
| Filtering | `Owner.get_all_tasks(pet_name=..., include_completed=...)` | Optional keyword filters: one pet's tasks (case-insensitive) and/or hide completed tasks. The scheduler itself uses `include_completed=False` plus a due-date check. |
| Conflict detection | `Scheduler.detect_conflicts()` | Pairwise interval-overlap test (`itertools.combinations`) on requested `"HH:MM"` slots. Returns warning strings on `Schedule.warnings` instead of crashing — conflicts never block the plan. Back-to-back tasks are not flagged. |
| Recurring tasks | `Task.next_occurrence()`, `Pet.mark_task_complete()` | Completing a daily/weekly task auto-creates a fresh copy due `+1 day` / `+1 week` (via `timedelta`, so month/year rollovers are handled). `build_schedule` only includes tasks with `due_date <= today`, so tomorrow's copy never leaks into today's plan. |

All four behaviors are demonstrated in `main.py` and covered by `tests/test_pawpal.py` (7 tests).

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
