# Website Spec Plan

## Goal
Write a spec in `agent_docs/` for my site so LLM coding agents can implement it.
Use `README.md` in this folder and this plan as the governing inputs.
Keep the spec itself in `agent_docs/`.

The site has a homepage with contact and gift links.
The site has a works index with section headings I can customize.
When I add a new work in the works area, it should appear in the index automatically. Each work uses its folder name, published at `/<folder-name>`. A work may name one section from the site config.
Work pages need linked body headings, a generated section index, work-to-work links, backlinks, and external link treatment readers can distinguish without relying on color alone.

## Scopes 

### web-rules.md
- Specify accessibility and interoperability standards

### shape.md
- Describe the relationships among elements and general UX

### look.md
- Describe the UI

### build.md
- Generate the static site

## Structure

- `plan.md` assigns scope and decision ownership.
- The scope docs in `agent_docs/` define the overview requirements for each scope.
- The examples in `agent_docs/examples/` define exact behavior and expected outcomes for unusual behavior, specific preferences, and edge cases.
- Read a scope doc and its examples together.

## Acceptance Criteria
- Review the `Goal` section against `web-rules.md`, `shape.md`, `look.md`, and `build.md`.
- Review `agent_docs/examples/README.md` coverage groups and named fixtures against those scope docs.
- Each scope has one owning doc.
- The scope docs and examples agree.
