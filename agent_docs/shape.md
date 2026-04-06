# Shape

## Purpose
Specify relationships and flow of use by author and reader.

## Decisions Owned
- How the author adds work
- How the author defines section names
- How a work gets its published path
- What pages people use
- How readers move within a work
- How works link to each other
- How readers move through the site
- How readers reach the author

## Requirements
1. The author adds works to a folder.
2. Adding a work there is enough to make it part of the site.
3. The author lists section names in `site.toml` in the order they should appear on `/works`.
4. A work may set `section` to one of those section names. If it does not, or if the name does not match, the work falls into `Other works`.
5. Each work derives its title from its folder name. The works index uses that same title.
6. Each work is published at `/<folder-name>` so work links stay short, direct, and slashless.
7. A work can be written in Markdown or HTML body content.
8. People using the site get a cover page, `/`; table of contents, `/works`; one work page for each work, and `/feed.xml`.
9. Every page (RSS feed is an exception) uses the shared site frame.
10. That frame lets readers navigate the site and contact or pay the author.

## Micro-Features
- `Heading self-links`: Each body heading gets an id from its visible text and a self-link.
- `Content nav sidebar`: Two or more top-level body headings add a Contents sidebar with links based on headings.
- `wikilinks`: A `[[...]]` link is a soft reference to a work. If it matches a work, link to that work's published path. A label in the link becomes the visible text. If it does not match a work, render plain text.
- `Backlinks`: A work-to-work link adds the source work title to a backlinks section on the destination work page. The backlinks section appears after the body content.

## Acceptance Checks
1. Build the examples named in `agent_docs/examples/README.md` and compare the results with each `expected.md`.
2. Inspect `/`, `/works`, and one work page.
