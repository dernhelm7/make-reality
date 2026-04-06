# Website Spec Plan

## Goal
Write a spec in `agent_docs/` for my site so LLM coding agents can implement it.
Use `README.md` in this folder and this plan as the governing inputs.
Keep the spec itself in `agent_docs/`.

The site has a homepage with contact and gift links.
The site has a works index with section headings I can customize.
When I add a new work in the works area, it should appear in the index automatically. Each work uses its folder name, publishes at `/<folder-name>`, and carries an explicit created date. A work may name one section from the site config.
Work pages need linked body headings, a generated section index, work-to-work links, backlinks, and external link treatment readers can distinguish without relying on color alone.

## Scopes 

### web-rules.md
- Accessibility and interoperability supporting rules

### shape.md
- Relationships and flow of use by author and reader: UX

### look.md
- Appearance: UI

### build.md
- Generate the static site

## Acceptance Criteria
- Adding a work is enough to make it show up on the site.
- Public page types are defined for the homepage, the works index, individual work pages, and the feed.
- Contact and gift links are available.
- Section names and short published paths are defined.
- Work pages define body heading links, generated section indexes, work-to-work links, and backlinks.
- External links are distinguishable from internal work links without relying on color alone.
- Each doc is a complete set of instructions for its own scope.
- Each requirement is defined in only one place.
- The spec supports adding works after launch.
- `build.md` is enough to define code that handles local build and publication .
