# AGENTS.md

This file sets general policy for agents working on this repo. 

## Guidance

"Do less, do it better."

- Use plain English.
- Say what to do. Fix issues by rewriting so correct behavior is the default. The rewrite is the prevention. Use a negative instruction only if the contrast removes ambiguity.
- Check the repo before assuming what exists.
- Take product decisions from the files in `agent_docs/`.
- Update the spec to keep it aligned with the code.
- Keep this file repo-wide; put narrower guidance closer to the work.
- Fix root causes, not symptoms
- When editing, restate the central idea more efficiently. Don't cut. Distill.


## Standards

Apply these standards to planning, specification, and implementation.

- Choose the simplest design that meets the need.
- Keep sections, functions, and modules small and focused.
- Add abstraction only when repetition or expected change justifies it.
- Validate close to the source and fail with clear, actionable errors.
- When behavior is unclear, degrade gracefully or stop cleanly.
- When behavior is unspecified, make the smallest reasonable choice and mark it as a guess.

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
- If a task changes acceptance behavior, update the affected acceptance checks and example expectations in the same change.

## Done Means

- The changed behavior matches the owning spec.
- The spec, examples, and implementation agree.
- Relevant acceptance checks, examples, and validation steps are updated or explicitly confirmed unchanged.


## Hard Constraints

- No build-generated JavaScript in the shared site output; I wannt the site dependencies super light and clean. A specific work may use author-provided JavaScript. 
