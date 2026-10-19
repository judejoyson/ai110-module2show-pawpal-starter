"""Temporary testing ground for PawPal+ core logic.

Run with: python main.py
The Streamlit app (app.py) is the real UI; this just proves the backend works.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_tasks(heading: str, tasks: list[Task]) -> None:
    """Print a labeled list of tasks with their preferred times and status."""
    print(f"\n{heading}")
    for t in tasks:
        when = t.preferred_time or "anytime"
        status = "done" if t.completed else "pending"
        print(f"  {when:<8} {t.title:<20} {t.duration_minutes:>3} min  {t.priority:<7} [{status}]")


def main() -> None:
    # One owner with a 90-minute care budget and two pets.
    owner = Owner(name="Jordan", available_minutes=90)
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks added deliberately OUT of time order to prove sorting works.
    mochi.add_task(Task("Evening walk", 30, "high", preferred_time="18:00"))
    luna.add_task(Task("Play session", 25, "medium", preferred_time="15:30"))
    mochi.add_task(Task("Morning walk", 30, "high", preferred_time="07:30"))
    luna.add_task(Task("Give meds", 10, "high", preferred_time="08:00"))
    mochi.add_task(Task("Brush coat", 15, "low"))  # no preferred time -> sorts last
    # Deliberate conflict: 07:45 feeding overlaps the 07:30-08:00 morning walk.
    luna.add_task(Task("Breakfast", 15, "high", preferred_time="07:45"))
    done = Task("Clean litter box", 10, "medium", preferred_time="09:00")
    done.mark_complete()
    luna.add_task(done)

    scheduler = Scheduler(owner, start_hour=8)

    # --- Sorting demo: tasks were added 18:00, 15:30, 07:30, 08:00, ... ---
    all_tasks = [task for _, task in owner.get_all_tasks()]
    print_tasks("All tasks in the order they were added:", all_tasks)
    print_tasks("Sorted by time (sort_by_time):", scheduler.sort_by_time(all_tasks))

    # --- Filtering demos ---
    luna_tasks = [task for _, task in owner.get_all_tasks(pet_name="Luna")]
    print_tasks("Filtered: Luna's tasks only:", luna_tasks)

    pending = [task for _, task in owner.get_all_tasks(include_completed=False)]
    print_tasks("Filtered: pending tasks only (completed hidden):", pending)

    # --- Recurrence demo: completing a daily task spawns tomorrow's copy ---
    print("\nMarking Luna's daily 'Give meds' complete...")
    next_task = luna.mark_task_complete("Give meds")
    if next_task:
        print(f"  Auto-created next occurrence: due {next_task.due_date} ({next_task.frequency})")
    print_tasks(
        "Luna's tasks after completion (today done, tomorrow pending):",
        [task for _, task in owner.get_all_tasks(pet_name="Luna")],
    )

    # --- Full schedule, as before ---
    schedule = scheduler.build_schedule()
    print()
    print(f"Today's Schedule for {owner.name} ({schedule.day.isoformat()})")
    print(f"Budget: {owner.available_minutes} min | Scheduled: {schedule.total_minutes} min")
    print("-" * 72)
    print(f"{'Time':<13} {'Pet':<7} {'Task':<20} {'Min':>4}  {'Priority':<8}")
    print("-" * 72)
    for row in schedule.to_display_rows():
        time_range = row["Time"].replace("–", "-")
        print(
            f"{time_range:<13} {row['Pet']:<7} {row['Task']:<20} "
            f"{row['Duration (min)']:>4}  {row['Priority']:<8}"
        )
    print("-" * 72)

    scheduled_titles = {e.task.title for e in schedule.entries}
    skipped = [
        t.title
        for _, t in owner.get_all_tasks(include_completed=False)
        if t.due_date <= schedule.day and t.title not in scheduled_titles
    ]
    if skipped:
        print(f"Skipped (not enough time): {', '.join(skipped)}")

    # --- Conflict detection: warnings, never crashes ---
    if schedule.warnings:
        print("\nWARNING - preferred-time conflicts detected:")
        for warning in schedule.warnings:
            print(f"  ! {warning}")


if __name__ == "__main__":
    main()
