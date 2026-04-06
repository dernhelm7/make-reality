# Website Spec Plan

## Goal
Write a spec in `agent_docs/` for my site so LLM coding agents can implement it.
Use `README.md` in this folder and this plan as the governing inputs.
Keep the spec itself in `agent_docs/`.

The site has a homepage with contact and gift links.
The site has a works index with section headings I can customize.
When I add a new work in the works area, it should appear in the index automatically. Each work uses its folder name, publishes at `/<folder-name>`, and carries an explicit created date. A work may name one section from the site config.

## Scopes 

### web-rules.md
- Say what the built site gives the browser, the reader, and other systems.

### shape.md
- Say how people use the site: how the author adds work, what pages people use, and how readers move through the site and reach the author.

### look.md
- Say how the cover page, the table of contents, and the reading page hold together visually.

### build.md
- Say how site files become published output, and what the build does when something goes wrong.

## Acceptance Criteria
- Adding a work is enough to make it show up on the site.
- Public page types are defined for the homepage, the works index, individual work pages, and the feed.
- Contact and gift links are available.
- Section names and short published paths are defined.
- Each doc is a complete set of instructions for its own scope.
- Each requirement is defined in only one place.
- The spec supports adding works after launch.
- `build.md` is enough to define the local build and publication contract.
