# AGENTS.md

This file sets general policy for agents working on this repo. 

## Guidance

"Do less, do it better."

- Use concrete nouns, name the action or choice that changes the outcome, and stop once you have named the lever that matters.
- Say what to do. Change the structure so correct behavior is the default. Use a negative instruction only if the contrast removes ambiguity.
- Check the repo before assuming what exists.
- Update the spec to keep it aligned with the code.
- Keep this file repo-wide; put narrower guidance closer to the work.
- Solve the right problem. Fix the origin, not the output.
- Follow the grain of the problem. Work with the natural structure.
- Frame the central idea efficiently. Don't just cut extra words. Distill the essence.


## Standards

Apply these standards to planning, specification, and implementation.

- Choose the simplest design that meets the need.
- Keep sections, functions, and modules small and focused.
- Add abstraction only when necessary. If edge cases multiply, work at a better level of abstraction.
- Make robustness a consequence of the design. Prefer designs where bad states cannot be constructed over designs that only detect or reject them later.
- When behavior is unclear, degrade gracefully or stop cleanly.

## Read Order

- Start with `agent_docs/README.md`.
- Read `agent_docs/plan.md` to determine which spec docs in `agent_docs/` have the relevant scope, ownership, or acceptance criteria for the decision you are changing.

## Working Contract

- Keep each requirement owned in one document.
- When code changes behavior, update the owning spec in the same task.
- When a task touches a documented rule, update the matching example under `agent_docs/examples/` if one exists.
- If the repo does not yet contain a needed command or check, say so plainly instead of inventing one.

## Validation

- Run the most relevant local validation commands that already exist in the repo before finishing.
- For spec-only changes, review the affected docs and examples for duplicated or conflicting requirements.
- Do not restate requirements in validation or acceptance checks.
- If a task changes acceptance behavior, update the affected acceptance checks and example expectations in the same change.

## Done Means

- The changed behavior matches the owning spec.
- The spec, examples, and implementation agree.
- Relevant acceptance checks, examples, and validation steps are updated or explicitly confirmed unchanged.
- Correct behavior is described. Negative instructions are used only when the contrast removes ambiguity.
- Concrete nouns are used, the action or choice that changes the outcome is named, and instructions stop once the lever that matters is named.
- any rule that got inverted or edited, but could instead be deleted, is deleted.


## Hard Constraints

- No build-generated JavaScript in the shared site output; I wannt the site dependencies super light and clean. A specific work may use author-provided JavaScript. 
- Use concrete nouns, name the action or choice that changes the outcome, and stop once you have named the lever that matters.

