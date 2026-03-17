# AGENTS.md

This file sets repo-wide policy for humans and agents. The repo builds a static personal publishing site based on the product idea in `aim.md`.

## Guidance

"Do less, do it better."

- Use plain English.
- Say what to do. Use a negative instruction only when the contrast removes ambiguity.
- Fix issues with a minimal update to the wording so correct behavior becomes the new default; remove anything not needed to make the point clear.
- Check the repo before assuming what exists.
- Take product decisions from the files in `agent_docs/`.
- Update the spec to keep it aligned with the code.
- Keep this file repo-wide; put narrower guidance closer to the work.
- Fix root causes, not symptoms

## Standards

Apply these standards to planning, specification, and implementation.

- Choose the simplest design that meets the need.
- Keep sections, functions, and modules small and focused.
- Add abstraction only when repetition or expected change justifies it.
- Validate close to the source and fail with clear, actionable errors.
- When behavior is unclear, degrade gracefully or stop cleanly.
- When behavior is unspecified, make the smallest reasonable choice and mark it as a guess.


## Hard Constraints

- No JavaScript in generated output (local exceptions only if the scope and justification are explicit).
