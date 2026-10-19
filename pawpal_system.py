"""PawPal+ core classes.

Data classes (Task, Pet, Owner, ScheduledTask, Schedule) hold state;
Scheduler is the logic layer that turns an Owner's tasks into a daily plan.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

# Single source of truth for priority ordering (higher = more important).
PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    frequency: str = "daily"  # "once" | "daily" | "weekly"
    preferred_time: str = ""  # e.g., "morning", "evening", or "" for no preference
    completed: bool = False

    def priority_score(self) -> int:
        """Return a numeric score for sorting, looked up in PRIORITY_SCORES.

        Unknown priority strings score 0 so they sort last instead of crashing.
        """
        return PRIORITY_SCORES.get(self.priority, 0)

    def mark_complete(self) -> None:
        """Mark this task as done so the scheduler skips it."""
        self.completed = True


@dataclass
class Pet:
    """A pet with its own list of care tasks."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the first task matching the given title (case-insensitive)."""
        for task in self.tasks:
            if task.title.lower() == title.lower():
                self.tasks.remove(task)
                return

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        return list(self.tasks)


@dataclass
class Owner:
    """The pet owner, their preferences, and their pets."""

    name: str
    available_minutes: int = 120
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> "Pet | None":
        """Return the owner's pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every pet's tasks together as (pet, task) pairs.

        The pairing keeps pet attribution, so the scheduler can plan across
        all pets at once and still say which pet each task belongs to.
        """
        return [(pet, task) for pet in self.pets for task in pet.tasks]


@dataclass
class ScheduledTask:
    """A task placed into a schedule at a specific time, with a reason."""

    task: Task
    pet_name: str
    start_time: time
    end_time: time
    reason: str = ""


@dataclass
class Schedule:
    """A day's plan: ordered scheduled tasks plus explanations."""

    day: date = field(default_factory=date.today)
    entries: list[ScheduledTask] = field(default_factory=list)

    @property
    def total_minutes(self) -> int:
        """Total scheduled time, computed from entries so it can never drift."""
        return sum(e.task.duration_minutes for e in self.entries)

    def add_entry(self, entry: ScheduledTask) -> None:
        """Append an entry to the schedule."""
        self.entries.append(entry)

    def explain(self) -> str:
        """Return a human-readable explanation of why each task was chosen."""
        if not self.entries:
            return "No tasks were scheduled — add tasks or increase available time."
        lines = [f"Daily plan for {self.day.isoformat()} ({self.total_minutes} min total):"]
        for e in self.entries:
            lines.append(
                f"  {e.start_time.strftime('%H:%M')} — {e.task.title} for {e.pet_name} "
                f"({e.task.duration_minutes} min): {e.reason}"
            )
        return "\n".join(lines)

    def to_display_rows(self) -> list[dict]:
        """Return rows suitable for st.table / st.dataframe in the UI."""
        return [
            {
                "Time": f"{e.start_time.strftime('%H:%M')}–{e.end_time.strftime('%H:%M')}",
                "Pet": e.pet_name,
                "Task": e.task.title,
                "Duration (min)": e.task.duration_minutes,
                "Priority": e.task.priority,
                "Why": e.reason,
            }
            for e in self.entries
        ]


class Scheduler:
    """Builds a daily Schedule from all of an owner's pets' tasks."""

    def __init__(self, owner: Owner, start_hour: int = 8):
        self.owner = owner
        self.start_hour = start_hour

    def build_schedule(self, available_minutes: int | None = None) -> Schedule:
        """Plan the day across every pet, highest priority first.

        Reads tasks via owner.get_all_tasks() so pets share one time budget.
        Defaults to the owner's available_minutes when no override is given.
        """
        budget = available_minutes if available_minutes is not None else self.owner.available_minutes
        pending = [(pet, task) for pet, task in self.owner.get_all_tasks() if not task.completed]
        ordered = self._sort_tasks(pending)

        schedule = Schedule()
        remaining = budget
        cursor = datetime.combine(schedule.day, time(hour=self.start_hour))

        for pet, task in ordered:
            if not self._fits_in_time(task, remaining):
                continue
            end = cursor + timedelta(minutes=task.duration_minutes)
            reason = (
                f"{task.priority} priority for {pet.name}, "
                f"fits in the {remaining} min remaining"
            )
            schedule.add_entry(
                ScheduledTask(
                    task=task,
                    pet_name=pet.name,
                    start_time=cursor.time(),
                    end_time=end.time(),
                    reason=reason,
                )
            )
            cursor = end
            remaining -= task.duration_minutes

        return schedule

    def _sort_tasks(self, pet_tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Sort by priority (high first), then shorter tasks first as tie-breaker."""
        return sorted(
            pet_tasks,
            key=lambda pair: (-pair[1].priority_score(), pair[1].duration_minutes),
        )

    def _fits_in_time(self, task: Task, remaining: int) -> bool:
        """Return True if the task fits in the remaining minutes."""
        return task.duration_minutes <= remaining
