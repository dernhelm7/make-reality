# Website Spec Plan

## Goal
Write a spec in 'agent_docs/' for my site which can be implemented by LLM coding agents.
Use `README.md` in this folder and this plan as the governing inputs for that spec.
Keep the spec itself in `agent_docs/`.

There's a main page, with contact and gift links.
There's an index of works with subheadings I can customize.
There's a folder where I can add new works, and it will be shown in the index of works automatically using the folder name and an explicit created timestamp. But if I customize it, that overrides the defaults.

## Scopes 

### web-rules.md
- Specify the generated web standards for the published output: accessibility, progressive enhancement, semantics, and interoperability.

### shape.md
- Specify the page relationships, page structure, and navigation.

### bones.md
- Specify the site and work content models: what the site and a work are, what metadata they carry, and how defaults and overrides work.

### look.md
- Specify the visual system.

### build.md
- Specify the build process, outputs, and validation behavior.

## Guidance

- Use the Aim section in `README.md` to understand product intent. Clarify open questions.
- Make each file the source of truth for its own decision scope.
- When one doc needs a concept owned by another doc, refer to that doc instead of redefining it.
- If a requirement could fit in more than one doc, assign it once to the narrowest scope and have the other docs use it.
- Use a standard format: Purpose, Decisions Owned, Requirements, Acceptance Checks.
- Use direct, positive language; state what the site does. Reserve negative requirements for constraints and explicit exceptions.
- Use traditional section numbering.
- Write testable requirements.
- Mark guesses explicitly. Resolve guesses before calling the plan complete.

## Acceptance Criteria
- Page types are defined: `/`, `/works`, and `/<slug>`.
- A public RSS feed is defined at `/feed.xml`.
- Contact and gift links are available.
- Default indexing and how customization overrides it are defined.
- Each doc is a complete set of instructions for its own scope.
- Each requirement is defined in only one place; prevent conflicting definitions.
- Site structure and content model support adding works post-launch.
- `build.md` is sufficient to build the site.
