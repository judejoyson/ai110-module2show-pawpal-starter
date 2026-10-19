import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

# Streamlit reruns this script top-to-bottom on every interaction, so the
# Owner must live in st.session_state or it would be recreated empty each time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

owner = st.session_state.owner
scheduler = Scheduler(owner)

st.subheader("Owner & Pets")
owner.name = st.text_input("Owner name", value=owner.name)

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    st.write("")
    st.write("")
    add_pet_clicked = st.button("Add pet")

if add_pet_clicked:
    if not pet_name.strip():
        st.error("Pet name cannot be empty.")
    elif owner.get_pet(pet_name) is not None:
        st.info(f"{pet_name} is already one of {owner.name}'s pets.")
    else:
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
        st.success(f"Added {pet_name} the {species}!")

if owner.pets:
    st.caption("Current pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))

st.divider()

st.markdown("### Tasks")

if not owner.pets:
    st.info("Add a pet first — tasks belong to a pet.")
else:
    task_pet_name = st.selectbox("For which pet?", [p.name for p in owner.pets])
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    col4, col5 = st.columns(2)
    with col4:
        preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

    if st.button("Add task"):
        pet = owner.get_pet(task_pet_name)
        pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                frequency=frequency,
                preferred_time=preferred_time.strip(),
            )
        )
        st.success(f"Added '{task_title}' for {pet.name} ({frequency}).")

    # Mark-complete controls come BEFORE the task table so the table below
    # already reflects the change within the same rerun.
    pending = owner.get_all_tasks(include_completed=False)
    if pending:
        done_col1, done_col2 = st.columns([3, 1])
        with done_col1:
            done_choice = st.selectbox(
                "Mark a task complete",
                [f"{pet.name} — {task.title}" for pet, task in pending],
            )
        with done_col2:
            st.write("")
            st.write("")
            if st.button("Done ✔"):
                done_pet_name, done_title = done_choice.split(" — ", 1)
                next_task = owner.get_pet(done_pet_name).mark_task_complete(done_title)
                if next_task is not None:
                    st.success(
                        f"Completed! Next occurrence auto-created for {next_task.due_date} "
                        f"({next_task.frequency})."
                    )
                else:
                    st.success("Completed! One-off task — nothing rescheduled.")

    # Task list with filtering (Owner.get_all_tasks) and sorting (Scheduler.sort_by_time).
    st.markdown("#### Task list")
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        pet_filter = st.selectbox("Show", ["All pets"] + [p.name for p in owner.pets])
    with fcol2:
        show_completed = st.checkbox("Include completed", value=True)
    with fcol3:
        sort_by_time = st.checkbox("Sort by preferred time")

    pairs = owner.get_all_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        include_completed=show_completed,
    )
    if pairs:
        pet_of = {id(task): pet for pet, task in pairs}
        tasks = [task for _, task in pairs]
        if sort_by_time:
            tasks = scheduler.sort_by_time(tasks)
        st.table(
            [
                {
                    "Pet": pet_of[id(task)].name,
                    "Task": task.title,
                    "Time": task.preferred_time or "anytime",
                    "Duration (min)": task.duration_minutes,
                    "Priority": task.priority,
                    "Frequency": task.frequency,
                    "Due": task.due_date.strftime("%b %d"),
                    "Done": "✅" if task.completed else "—",
                }
                for task in tasks
            ]
        )
    else:
        st.info("No tasks match the current filters.")

st.divider()

st.subheader("Build Schedule")

owner.available_minutes = int(
    st.number_input(
        "Available minutes today", min_value=10, max_value=600, value=owner.available_minutes
    )
)
start_hour = st.slider("Start hour", min_value=5, max_value=20, value=8)

if st.button("Generate schedule"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        schedule = Scheduler(owner, start_hour=start_hour).build_schedule()

        # Conflict warnings first: visible before the plan, specific enough to act on,
        # but non-blocking — the plan below still builds.
        for conflict in schedule.warnings:
            st.warning(f"⏰ Time conflict: {conflict}. Consider adjusting one of these times.")

        if schedule.entries:
            st.success(
                f"Scheduled {schedule.total_minutes} of {owner.available_minutes} "
                f"available minutes across {len(schedule.entries)} task(s)."
            )
            st.table(schedule.to_display_rows())
            with st.expander("Why this plan?"):
                st.text(schedule.explain())
            scheduled_titles = {e.task.title for e in schedule.entries}
            skipped = [
                f"{task.title} ({pet.name})"
                for pet, task in owner.get_all_tasks(include_completed=False)
                if task.due_date <= schedule.day and task.title not in scheduled_titles
            ]
            if skipped:
                st.warning("Skipped (not enough time): " + ", ".join(skipped))
        else:
            st.warning("Nothing fit the available time. Add more time or shorter tasks.")
