"""Tests for PawPal+ core classes.

Run with: python -m pytest
"""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status():
    task = Task("Give meds", duration_minutes=10, priority="high")
    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Morning walk", duration_minutes=30, priority="high"))

    assert len(pet.get_tasks()) == 1


def test_completing_daily_task_creates_next_occurrence():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Morning walk", 30, "high", frequency="daily"))

    next_task = pet.mark_task_complete("Morning walk")

    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert len(pet.get_tasks()) == 2  # today's (done) + tomorrow's (pending)


def test_completing_weekly_task_recurs_in_seven_days():
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Nail trim", 15, "low", frequency="weekly"))

    next_task = pet.mark_task_complete("Nail trim")

    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(weeks=1)


def test_completing_once_task_does_not_recur():
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Vet visit", 60, "high", frequency="once"))

    assert pet.mark_task_complete("Vet visit") is None
    assert len(pet.get_tasks()) == 1  # no new instance created


def test_detects_overlapping_preferred_times_across_pets():
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Morning walk", 30, "high", preferred_time="07:30"))  # 07:30-08:00
    luna.add_task(Task("Breakfast", 15, "high", preferred_time="07:45"))  # 07:45-08:00

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "Morning walk" in warnings[0] and "Breakfast" in warnings[0]


def test_back_to_back_tasks_are_not_a_conflict():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Morning walk", 30, "high", preferred_time="07:30"))  # ends 08:00
    pet.add_task(Task("Feeding", 10, "high", preferred_time="08:00"))  # starts exactly then

    assert Scheduler(owner).detect_conflicts() == []


# --- Sorting correctness ---


def test_sort_by_time_returns_chronological_order():
    owner = Owner(name="Jordan")
    scheduler = Scheduler(owner)
    tasks = [  # deliberately out of order; one untimed
        Task("Evening walk", 30, "high", preferred_time="18:00"),
        Task("Brush coat", 15, "low"),  # no time -> must sort last
        Task("Morning walk", 30, "high", preferred_time="07:30"),
        Task("Lunch", 10, "medium", preferred_time="12:00"),
    ]

    ordered = scheduler.sort_by_time(tasks)

    assert [t.title for t in ordered] == ["Morning walk", "Lunch", "Evening walk", "Brush coat"]


# --- Conflict detection: duplicate (identical) times ---


def test_tasks_at_the_exact_same_time_are_flagged():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", preferred_time="08:00"))
    pet.add_task(Task("Feeding", 10, "high", preferred_time="08:00"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Feeding" in warnings[0]


def test_malformed_preferred_time_is_skipped_not_crashed():
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", preferred_time="8am"))  # not HH:MM
    pet.add_task(Task("Feeding", 10, "high", preferred_time="25:99"))  # impossible time

    assert Scheduler(owner).detect_conflicts() == []  # ignored, no exception


# --- Scheduling: priority, budget, and emptiness edge cases ---


def test_schedule_respects_priority_and_budget():
    owner = Owner(name="Jordan", available_minutes=40)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Brush coat", 20, "low"))  # added first, should lose
    pet.add_task(Task("Morning walk", 30, "high"))  # should be scheduled first
    pet.add_task(Task("Feeding", 10, "medium"))

    schedule = Scheduler(owner).build_schedule()

    titles = [e.task.title for e in schedule.entries]
    assert titles == ["Morning walk", "Feeding"]  # high first, then medium fills budget
    assert "Brush coat" not in titles  # low priority dropped: only 0 min left
    assert schedule.total_minutes <= owner.available_minutes


def test_owner_with_no_pets_builds_empty_schedule():
    schedule = Scheduler(Owner(name="Jordan")).build_schedule()

    assert schedule.entries == []
    assert schedule.total_minutes == 0
    assert "No tasks" in schedule.explain()


def test_pet_with_no_tasks_builds_empty_schedule():
    owner = Owner(name="Jordan")
    owner.add_pet(Pet(name="Mochi", species="dog"))

    schedule = Scheduler(owner).build_schedule()

    assert schedule.entries == []


def test_task_exactly_filling_budget_is_scheduled():
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    pet.add_task(Task("Morning walk", 30, "high"))  # exactly the budget

    schedule = Scheduler(owner).build_schedule()

    assert len(schedule.entries) == 1  # <= boundary, not <


# --- Recurrence: tomorrow's copy must not leak into today's plan ---


def test_completed_daily_task_is_not_rescheduled_today():
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Luna", species="cat")
    owner.add_pet(pet)
    pet.add_task(Task("Give meds", 10, "high", frequency="daily"))
    pet.mark_task_complete("Give meds")  # done today; copy auto-created for tomorrow

    schedule = Scheduler(owner).build_schedule()

    meds_entries = [e for e in schedule.entries if e.task.title == "Give meds"]
    assert meds_entries == []  # neither today's (done) nor tomorrow's (not due) copy


def test_mark_complete_with_unknown_title_returns_none():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30, "high"))

    assert pet.mark_task_complete("Swim lesson") is None
    assert len(pet.get_tasks()) == 1  # nothing added or removed


def test_unknown_priority_scores_zero_and_sorts_last():
    assert Task("Mystery", 10, "urgent!!").priority_score() == 0  # typo-proof, no crash
