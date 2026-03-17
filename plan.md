# Website Spec Plan

## Goal
Write a spec in 'agent_docs/' for my site which can be implemented by LLM coding agents.

There's a main page, with contact and gift links.
There's an index of works with subheadings I can customize.
There's a folder where I can add new works, and it will be shown in the index of works automatically using the folder name and an explicit created timestamp. But if I customize it, that overrides the defaults.

## Scopes 

### web-rules.md
- Specify the web standards the site must meet: accessibility, progressive enhancement, and interoperability constraints that the other docs must conform to.

### shape.md
- Specify the UX: relationships among pages, internal page structure, and navigation.

### bones.md
- Specify the content model: what a work is, what metadata it carries, and how content and assets are organized.

### look.md
- Specify the UI; the visual system for the site.

### build.md
- Specify how the site is built.

## Guidance

- Use `aim.md` to understand product intent. Clarify open questions.
- Make each file a self-contained contract for its own decision scope.
- Use a standard format: Purpose, Decisions Owned, Requirements, Acceptance Checks, and Open Questions.
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
