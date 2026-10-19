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

## ✨ Features

- **Multi-pet planning** — one owner, any number of pets, all sharing a single daily time budget (`Owner.get_all_tasks()` feeds the scheduler across every pet).
- **Priority-based scheduling** — high-priority tasks are placed first within the available minutes; tasks that don't fit are reported as skipped, never silently dropped.
- **Sorting by time** — tasks with `"HH:MM"` preferred times can be viewed in chronological order (`Scheduler.sort_by_time()`), with untimed tasks listed last.
- **Filtering** — view tasks for one pet or hide completed ones (`Owner.get_all_tasks(pet_name=..., include_completed=...)`).
- **Daily & weekly recurrence** — completing a recurring task auto-creates the next occurrence (+1 day or +1 week) without it leaking into today's plan.
- **Conflict warnings** — overlapping or identical preferred times produce specific, non-blocking warnings (`Scheduler.detect_conflicts()`); the plan still builds.
- **Explainable plans** — every scheduled slot carries a reason, and `Schedule.explain()` produces a human-readable justification of the whole day.
- **Two front ends, one engine** — a Streamlit app (`app.py`) and a terminal demo (`main.py`) drive the same `pawpal_system.py` core, which is covered by 17 pytest tests.

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

Run the suite from the project root:

```bash
python -m pytest

# Or with coverage:
pytest --cov
```

**What the tests cover** (17 tests in `tests/test_pawpal.py`):

- **Task basics** — completion flips status; adding a task grows the pet's list.
- **Sorting** — `sort_by_time` returns chronological "HH:MM" order with untimed tasks last.
- **Scheduling** — priority order is respected within the time budget; a task exactly equal to the budget is scheduled (boundary test); an owner with no pets or a pet with no tasks yields an empty schedule instead of crashing.
- **Recurrence** — completing a daily/weekly task creates one copy due +1 day / +1 week; "once" tasks don't recur; tomorrow's copy never leaks into today's plan; completing an unknown title safely returns `None`.
- **Conflict detection** — identical and overlapping preferred times are flagged (exactly one warning per pair, across different pets too); back-to-back tasks are not false positives; malformed times like "8am" are skipped, never raised.
- **Robustness** — an unknown priority string scores 0 and sorts last instead of crashing.

Output of a successful run:

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\joyso\ai110-module2show-pawpal-starter
collected 17 items

tests\test_pawpal.py .................                                   [100%]

============================= 17 passed in 0.05s ==============================
```

**Confidence level: ★★★★☆ (4/5).** The scheduling core — priority, budget boundaries, recurrence, and conflict detection — is covered including its edge cases, and every behavior shown in the demo is pinned by a test. One star withheld because the Streamlit layer (`app.py`) is untested — session-state handling and display formatting are only verified manually — and multi-day scenarios (e.g., a weekly task chain over several completions) haven't been exercised.

## 📐 Smarter Scheduling

Four logic upgrades beyond the basic greedy scheduler, each with the method that implements it:

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | `Scheduler.sort_by_time()`, `Scheduler._sort_tasks()` | `sort_by_time` orders tasks by their `"HH:MM"` preferred time using a `lambda` key (zero-padded strings sort chronologically; untimed tasks sort last via a `"99:99"` sentinel). `_sort_tasks` orders the actual plan by priority, shorter duration breaking ties. |
| Filtering | `Owner.get_all_tasks(pet_name=..., include_completed=...)` | Optional keyword filters: one pet's tasks (case-insensitive) and/or hide completed tasks. The scheduler itself uses `include_completed=False` plus a due-date check. |
| Conflict detection | `Scheduler.detect_conflicts()` | Pairwise interval-overlap test (`itertools.combinations`) on requested `"HH:MM"` slots. Returns warning strings on `Schedule.warnings` instead of crashing — conflicts never block the plan. Back-to-back tasks are not flagged. |
| Recurring tasks | `Task.next_occurrence()`, `Pet.mark_task_complete()` | Completing a daily/weekly task auto-creates a fresh copy due `+1 day` / `+1 week` (via `timedelta`, so month/year rollovers are handled). `build_schedule` only includes tasks with `due_date <= today`, so tomorrow's copy never leaks into today's plan. |

All four behaviors are demonstrated in `main.py` and covered by `tests/test_pawpal.py` (17 tests).

## 📸 Demo Walkthrough

### The UI at a glance

Launch with `streamlit run app.py`. The page has three sections, top to bottom:

- **Owner & Pets** — set the owner's name and add pets (name + species). Duplicate names are rejected with a message; a caption lists current pets. The owner lives in `st.session_state`, so everything persists as you interact.
- **Tasks** — pick a pet, then enter a title, duration, priority, an optional preferred time ("HH:MM"), and a frequency (daily/weekly/once). A dropdown + **Done ✔** button marks any pending task complete — for recurring tasks, a success banner confirms the auto-created next occurrence and its due date. The task list below supports filtering (per pet, show/hide completed) and a "Sort by preferred time" toggle.
- **Build Schedule** — set the available minutes and start hour, then **Generate schedule**.

### Example workflow

1. Add two pets: **Mochi** (dog) and **Luna** (cat).
2. For Mochi, add "Morning walk" — 30 min, high priority, preferred time 07:30, daily.
3. For Luna, add "Breakfast" — 15 min, high priority, preferred time **07:45** (deliberately overlapping the walk), and "Play session" — 25 min, medium, no preferred time.
4. In the task list, tick **Sort by preferred time**: the table reorders chronologically with untimed tasks last. Switch the filter to "Luna" to see only her tasks.
5. Mark Luna's daily "Breakfast" complete with **Done ✔**: a green banner confirms tomorrow's copy was auto-created, and the list now shows today's ✅ plus tomorrow's pending copy.
6. Set 60 available minutes, start hour 8, and click **Generate schedule**.

### What the Scheduler shows in step 6

- A yellow **conflict warning** appears first: the 07:30–08:00 walk overlaps the 07:45 breakfast, with both pets and times named — but the plan still builds below it (warnings never block).
- A green **success banner** summarizes minutes used vs. available.
- The **schedule table** lists tasks in priority order with assigned time slots and a "Why" column; a "Why this plan?" expander gives the full explanation.
- Tasks that didn't fit the budget are listed as **skipped** — and the completed breakfast (plus its tomorrow copy) correctly appears nowhere in today's plan.

### Sample CLI output

The same engine runs in the terminal — this excerpt from `python main.py` shows the generated plan and a conflict warning (full run in [Sample Output](#%EF%B8%8F-sample-output) above):

```
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

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
