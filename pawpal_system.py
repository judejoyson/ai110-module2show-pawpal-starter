"""PawPal+ core classes.

Skeleton only — class names, attributes, and empty method stubs from diagrams/uml.mmd.
Implement the logic in small increments, then wire it into app.py.
"""

from dataclasses import dataclass, field
from datetime import date, time


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    is_recurring: bool = False
    preferred_time: str = ""  # e.g., "morning", "evening", or "" for no preference

    def priority_score(self) -> int:
        """Return a numeric score for sorting (higher = more important)."""
        pass


@dataclass
class Pet:
    """A pet with its own list of care tasks."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove the first task matching the given title."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        pass


@dataclass
class Owner:
    """The pet owner, their preferences, and their pets."""

    name: str
    available_minutes: int = 120
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def get_pet(self, name: str) -> Pet:
        """Return the owner's pet with the given name."""
        pass


@dataclass
class ScheduledTask:
    """A task placed into a schedule at a specific time, with a reason."""

    task: Task
    start_time: time
    end_time: time
    reason: str = ""


@dataclass
class Schedule:
    """A day's plan: ordered scheduled tasks plus explanations."""

    day: date = field(default_factory=date.today)
    entries: list[ScheduledTask] = field(default_factory=list)
    total_minutes: int = 0

    def add_entry(self, entry: ScheduledTask) -> None:
        """Append an entry and update the running total."""
        pass

    def explain(self) -> str:
        """Return a human-readable explanation of why each task was chosen."""
        pass

    def to_display_rows(self) -> list[dict]:
        """Return rows suitable for st.table / st.dataframe in the UI."""
        pass


class Scheduler:
    """Builds a daily Schedule from a pet's tasks under the owner's constraints."""

    def __init__(self, owner: Owner, start_hour: int = 8):
        self.owner = owner
        self.start_hour = start_hour

    def build_schedule(self, pet: Pet, available_minutes: int) -> Schedule:
        """Choose and order tasks that fit the available time, highest priority first."""
        pass

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by priority (and tie-breakers like duration)."""
        pass

    def _fits_in_time(self, task: Task, remaining: int) -> bool:
        """Return True if the task fits in the remaining minutes."""
        pass
