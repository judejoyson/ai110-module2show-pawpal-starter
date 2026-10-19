# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
- Add a pet, schedule a walk, and see today's tasks are the three core actions a user should be able to perform, so I designed six classes around them:
  - **Owner** — holds the user's name, how many minutes they have available, their preferences, and their list of pets. Responsible for adding and looking up pets.
  - **Pet** — holds basic pet info (name, species, age) and owns its list of care tasks. Responsible for adding, removing, and returning tasks.
  - **Task** — a single care activity (walk, feeding, meds) with a title, duration in minutes, and priority. It knows how to convert its priority into a numeric score for sorting.
  - **Scheduler** — the "brains" of the app. Given a pet and a time budget, it sorts tasks by priority, skips ones that don't fit the remaining time, and produces a Schedule. Sorting and fit-checking are private helpers because the UI only needs `build_schedule`.
  - **Schedule** — the output: a day's plan made of ordered entries, with methods to explain the reasoning and format rows for the Streamlit table.
  - **ScheduledTask** — wraps a Task with its assigned start/end time and a short reason explaining why it was placed there, which is what makes the plan explainable.
- I kept data classes (Owner, Pet, Task, Schedule, ScheduledTask) separate from the one logic class (Scheduler) so the scheduling algorithm can change without touching how data is stored.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
- Yes. I asked my AI assistant to review the class skeleton for missing relationships and bottlenecks, and I made four changes based on its feedback:
  1. **`Scheduler.build_schedule` now defaults to the owner's `available_minutes`** instead of requiring the caller to pass a time budget. The review pointed out there were two sources of truth for available time (the Owner attribute and the method parameter), which could contradict each other. Now the owner's value is the default and the parameter is only an override.
  2. **`Owner.get_pet` return type changed from `Pet` to `Pet | None`** because there is nothing valid to return when no pet matches the name — the old signature hid a possible crash.
  3. **`Schedule.total_minutes` changed from a stored attribute to a computed property.** As a stored field, every method that touched `entries` had to remember to update it or the total would silently drift. Computing it from the entries removes that sync bug entirely.
  4. **Added a `PRIORITY_SCORES` constant** so priority strings like "high" are mapped to numbers in one place instead of being magic values scattered through the code — a typo would have silently sorted tasks wrong.
- One issue the review raised that I deliberately did **not** fix yet: the Scheduler plans one pet at a time, so two pets sharing the same owner's time budget aren't coordinated. I'm deferring multi-pet scheduling to keep the first version simple.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
- I used AI at every stage, but in different ways:
  - **Design**: brainstormed the UML class diagram from the project requirements, then asked it to generate dataclass skeletons from that diagram.
  - **Review**: attached `pawpal_system.py` and asked it to look for missing relationships and logic bottlenecks — this caught the duplicate time-budget problem and the `total_minutes` sync bug before any logic existed.
  - **Implementation**: used agent mode to flesh out the method bodies, then asked how the `Scheduler` should retrieve tasks from the `Owner` (answer: hold an Owner reference and call `get_all_tasks()`, never reach into individual pets).
  - **Polish**: asked for a readable terminal format for the schedule (fixed-width columns instead of printing raw objects) and for drafting the pytest tests.
- The most helpful prompts were specific ones that attached the actual file and asked one focused question ("review this skeleton for missing relationships"), rather than broad ones like "make this better." Asking "how should X talk to Y" questions was more useful than asking for finished code, because the answer explained the design, not just the syntax.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
- The AI's original design had `build_schedule(pet, available_minutes)` — scheduling one pet at a time. Its own review flagged that multiple pets sharing one time budget weren't coordinated, and suggested a multi-pet refactor. I initially deferred that suggestion to keep the first version simple, and only accepted it once the assignment made multi-pet scheduling an explicit requirement — at which point the signature changed to read from `Owner.get_all_tasks()` instead of taking a pet. So the same suggestion was first rejected, then accepted, based on actual requirements rather than the AI's opinion.
- To verify the result, I didn't just trust the code: I ran `main.py` with two pets and checked the output by hand — high-priority tasks from *both* pets came first, the completed litter-box task was skipped, the 15-minute brushing task was dropped when the budget ran out, and the scheduled total (85 min) stayed under the 90-minute budget. I also ran `python -m pytest` to confirm the task-level behaviors pass.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
