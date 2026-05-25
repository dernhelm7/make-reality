# AGENTS.md

General policy for agents working in this repo. Keep this file repo-wide; put narrower guidance closer to the work.

"Do less, do it better."

## Read Order

- Start with `agent_docs/README.md`.
- Read `agent_docs/plan.md` to determine which spec docs in `agent_docs/` have the relevant scope, ownership, or acceptance criteria for the decision you are changing.

## Hard Constraints

- Build shared site behavior with browser-native HTML and CSS first. When a shared feature needs browser state or APIs, use a small isolated author-written script that calls browser APIs directly, stays scoped to that feature, and earns its main-thread cost.

## When planning or designing

- Choose the simplest design that meets the need.
- Keep sections, functions, and modules small and focused.
- Add abstraction only when necessary. If edge cases multiply, work at a better level of abstraction.
- Make robustness a consequence of the design. Prefer designs where bad states cannot be constructed over designs that only detect or reject them later.
- When behavior is unclear, degrade gracefully or stop cleanly.
- Solve the right problem. Fix the origin, not the output.
- Follow the grain of the problem. Work with the natural structure.
- Check the repo before assuming what exists. If a needed command or check does not yet exist, say so plainly instead of inventing one.

## When writing instructions, specs, or guidance

- Use concrete nouns, name the action or choice that changes the outcome, and stop once you have named the lever that matters.
- Say what to do. Change the structure so correct behavior is the default. Use a negative instruction only if the contrast removes ambiguity.
- Frame the central idea efficiently. Don't just cut extra words. Distill the essence.

## When changing code or specs

- Keep each requirement owned in one document.
- When code changes behavior, update the owning spec in the same task.
- When a task touches a documented rule, update the matching example under `agent_docs/examples/` if one exists.
- Treat `README.md` files as orientation documents, not implementation specs. Put build rules in `agent_docs/build.md`, product behavior in the matching scope doc, and fixture notes in `agent_docs/examples/`.
- Preserve `agent_docs/README.md` as the project aim. Edit it only when the user asks to change the aim.

## When finishing a task

- Run the most relevant local validation commands that already exist in the repo.
- For spec-only changes, review the affected docs and examples for duplicated or conflicting requirements.
- Do not restate requirements in validation or acceptance checks.
- If a task changes acceptance behavior, update the affected acceptance checks and example expectations in the same change.

### Done means

- The changed behavior matches the owning spec.
- The spec, examples, and implementation agree.
- Relevant acceptance checks, examples, and validation steps are updated or explicitly confirmed unchanged.
- any rule that got inverted or edited, but could instead be deleted, is deleted.
