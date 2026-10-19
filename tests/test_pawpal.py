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
