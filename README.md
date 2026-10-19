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

Terminal output from running `python main.py` (two pets sharing one 90-minute budget):

```
Today's Schedule for Jordan (2026-10-18)
Budget: 90 min | Scheduled: 85 min
------------------------------------------------------------------------
Time          Pet     Task                  Min  Priority
------------------------------------------------------------------------
08:00-08:10   Luna    Give meds              10  high
08:10-08:40   Mochi   Morning walk           30  high
08:40-09:00   Mochi   Training practice      20  medium
09:00-09:25   Luna    Play session           25  medium
------------------------------------------------------------------------
Skipped (not enough time): Brush coat

Why this plan:
  * Give meds: high priority for Luna, fits in the 90 min remaining
  * Morning walk: high priority for Mochi, fits in the 80 min remaining
  * Training practice: medium priority for Mochi, fits in the 50 min remaining
  * Play session: medium priority for Luna, fits in the 30 min remaining
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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler._sort_tasks`, `Task.priority_score` | Highest priority first; shorter duration breaks ties |
| Filtering | `Scheduler._fits_in_time`, `build_schedule` | Completed tasks skipped; tasks that don't fit the remaining budget are dropped |
| Conflict handling | `Scheduler.build_schedule` | Sequential time cursor — each task starts when the previous ends, so slots never overlap |
| Recurring tasks | `Task.frequency` | Field in place ("once"/"daily"/"weekly"); scheduler logic for it is future work |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
