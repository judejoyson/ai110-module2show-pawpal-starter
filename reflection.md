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
- The scheduler considers four constraints: the owner's daily time budget (`available_minutes`), task priority (high > medium > low, with shorter duration breaking ties), completion status plus due date (done tasks and tomorrow's auto-created recurring copies are excluded), and preferred times ("HH:MM" strings, used for conflict warnings).
- I ranked them by consequence: running out of time and missing a high-priority task (like meds) is worse than doing a task at a non-ideal hour. So the time budget and priority are hard constraints that decide *what* gets scheduled, while preferred times are soft — they generate warnings but never remove a task from the plan.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
- The main tradeoff: **the scheduler treats preferred times as advisory, not binding.** It packs tasks greedily by priority from the start hour, back-to-back, and separately runs `detect_conflicts()` on the *requested* times — so two tasks requested at overlapping times produce a warning message, but the plan still builds and nothing is auto-moved or dropped. The schedule the user gets can place an "evening walk" at 8:15 AM.
- This is reasonable because for a busy pet owner, the critical guarantee is "everything important fits in my available time" — a warning keeps the human in the loop to resolve timing themselves, whereas an auto-resolver could silently drop or move a meds dose, which is a worse failure. It also keeps the algorithm simple enough to test and explain (`reason` strings stay honest).
- A related, smaller tradeoff came from an AI simplification review of `detect_conflicts()`: I accepted replacing my manual index-slicing pair loop with `itertools.combinations` (more Pythonic *and* more readable), but rejected its O(n log n) sort-and-sweep optimization. The sweep is faster in theory, but at ~a dozen tasks the O(n²) pairwise check is instant, and the sweep's running-max-end subtlety is easy to get wrong — I chose the version I could verify over the clever one.

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
- The AI features that were most effective for this project: **agent mode with multi-file access** (the recurrence feature needed coordinated edits to `pawpal_system.py`, `main.py`, the tests, and the UML in one pass — doing that by hand across four files invites inconsistency), **attach-and-review** (having it audit my skeleton and later my conflict algorithm caught real design flaws cheaply), and **test drafting** (it proposed edge cases I hadn't listed, like the exact-budget boundary and malformed "25:99" times).
- Using separate chat sessions for the planning phases (algorithm brainstorming, test planning) kept each conversation focused on one job: a planning chat produces a *list of options to judge*, while an implementation chat produces *code*. Keeping them apart meant the planning output was a document I could carry over and prune, instead of the assistant immediately implementing its own first idea — the separation forced a decision point where I chose what actually got built.

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
- The suite has 17 tests in `tests/test_pawpal.py`, grouped around the behaviors where a bug would produce a *wrong plan* rather than a cosmetic glitch:
  - **Scheduling core**: priority order within the time budget, a task exactly equal to the budget (boundary test for `<=` vs `<`), and empty cases (owner with no pets, pet with no tasks) returning an empty schedule instead of crashing.
  - **Recurrence lifecycle**: daily completion creates a copy due +1 day, weekly +7 days, "once" doesn't recur — and the critical regression guard: after completing a daily task, it appears *zero* times in today's schedule (neither the done copy nor tomorrow's).
  - **Conflict detection contract**: identical and overlapping preferred times produce exactly one warning per pair; back-to-back tasks are not false positives; malformed times like "8am" are skipped silently, never raised.
  - **Robustness**: unknown priority strings score 0 instead of crashing; completing a nonexistent title returns `None`.
- These mattered because most of them encode *decisions*, not just behavior: the exact-fit test pins the `<=` choice, the back-to-back test pins "touching is not overlapping," and the zero-times recurrence test exists specifically because the double-scheduling bug is the easiest one to reintroduce.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
- About 4 out of 5. Everything the demo shows is pinned by a test, the boundaries I know about are covered, and the suite runs in under a tenth of a second so I actually run it after every change.
- What I'd test next: the **Streamlit layer** (`app.py` is only verified manually — session-state persistence and the mark-complete flow have no automated coverage), **multi-day recurrence chains** (complete a daily task three days in a row and check the due dates don't drift), **duplicate task titles** (the skipped-task display matches by title, so two pets with a task named "Give meds" could confuse the report), and schedules that would **run past midnight** (a 600-minute budget starting at 20:00 wraps the clock).

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
- The separation between data classes and the one logic class. Because `Task`, `Pet`, `Owner`, and `Schedule` only hold state, every new feature — filtering, sorting, recurrence, conflict detection — landed as a method with an obvious home, and none of them required reshaping the data model. The original six-class UML survived the entire build; only details were added. I'm also happy the plan stayed *explainable*: every scheduled slot carries a reason string, and warnings tell the owner exactly which two tasks collide and when.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
- Make the scheduler actually *use* preferred times for placement, not just for warnings — tasks should land near their requested "HH:MM" slot, with the greedy packer filling the gaps. I'd also add persistence (everything currently lives in memory/session state, so a browser refresh loses the pets) and replace title-based task lookup with stable IDs, which would fix the duplicate-title weakness in one move.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
- Being the "lead architect" with a powerful AI assistant means owning three things the AI can't own: **the requirements** (it suggested multi-pet scheduling early and I deferred it until the assignment actually required it — the same suggestion was wrong at one moment and right at another, and only I knew which), **the tradeoffs** (I rejected its faster sort-and-sweep conflict algorithm because at my scale, verifiable beats clever), and **the verification** (nothing it wrote counted as done until I'd run it and checked the output by hand). The AI was fastest at generating code and at critiquing code — but the decisions that shaped the system, and the responsibility for proving it correct, stayed with me. That division of labor is the whole skill: let the AI multiply execution, never delegate judgment.
