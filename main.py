"""Temporary testing ground for PawPal+ core logic.

Run with: python main.py
The Streamlit app (app.py) is the real UI; this just proves the backend works.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # One owner with a 90-minute care budget and two pets.
    owner = Owner(name="Jordan", available_minutes=90)
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna = Pet(name="Luna", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Tasks with different durations and priorities across both pets.
    mochi.add_task(Task("Morning walk", duration_minutes=30, priority="high"))
    mochi.add_task(Task("Brush coat", duration_minutes=15, priority="low"))
    mochi.add_task(Task("Training practice", duration_minutes=20, priority="medium"))
    luna.add_task(Task("Give meds", duration_minutes=10, priority="high"))
    luna.add_task(Task("Play session", duration_minutes=25, priority="medium"))

    scheduler = Scheduler(owner, start_hour=8)
    schedule = scheduler.build_schedule()

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
    skipped = [t.title for _, t in owner.get_all_tasks() if t.title not in scheduled_titles]
    if skipped:
        print(f"Skipped (not enough time): {', '.join(skipped)}")

    print()
    print("Why this plan:")
    for entry in schedule.entries:
        print(f"  * {entry.task.title}: {entry.reason}")


if __name__ == "__main__":
    main()
