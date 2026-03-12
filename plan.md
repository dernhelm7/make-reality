# Website Spec Plan

## Goal
Write a spec in 'agent_docs/' for my site which can be implemented by LLM coding agents.

There's a main page, with contact and payment options.
There's an index of works with subheadings I can customize.
There's a folder where I can add new works, and it will be shown in the index of works automatically using filename and creation timestamp. But if I customize it, that overrides the defaults.

## Scopes 

### web-rules.md
- Specify the web standards the site must meet: accessibility, progressive enhancement, and interoperability constraints that the other docs must conform to.

### shape.md
- Specify the UX: relationships among pages, internal page structure, and navigation.

### kinds.md
- Specify the content model: what a work is, what metadata it carries, and how content and assets are organized.

### look.md
- Specify the UI; the visual system for the site.

### build.md
- Specify how the site is built.

## Guidance

- Work by file scope.
- Use `aim.md` to understand product intent. Clarify open questions.
- Use direct, positive language
- Write testable requirements.
- Use negative requirements only for hard constraints or explicit exceptions.
- Mark guesses explicitly. Planning is not complete until they are resolved.

## Acceptance Criteria
- Page types are defined: `/`, `/works/`, and `/works/<slug>/`.
- Contact and payment options are available.
- Default indexing and how customization overrides it are defined.
- Each doc makes decisions limited to its own scope.
- Each requirement is defined in only one place; prevent conflicting definitions.
- Site structure and content model support adding works post-launch.
- `build.md` is sufficient to build the site.
