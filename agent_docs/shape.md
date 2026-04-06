# Shape

## Purpose
This document says how people use the site.

## Decisions Owned
- How the author adds work
- How the author defines section names
- How a work gets its published path
- What pages people use
- How readers move through the site
- How readers reach the author

## Requirements
1. The author adds works to a folder.
2. Adding a work there is enough to make it part of the site.
3. The author lists section names in `site.toml` in the order they should appear on `/works`.
4. A work may set `section` to one of those section names. If it does not, or if the name does not match, the work falls into `Other works`.
5. Each work derives its title from its folder name. The works index uses that same title.
6. Each work is published at `/<folder-name>` so work links stay short, direct, and slashless.
7. Each work carries an explicit created date.
8. A work can be written in Markdown or HTML body content.
9. People using the site get `/`, `/works`, one work page for each work, and `/feed.xml`.
10. `/` is the cover page. `/works` is the table of contents. A work page is where one work is read.
11. Every interface page (RSS feed is an exception) uses the shared site frame.
12. That frame lets readers navigate the site and contact or pay the author.

## Acceptance Checks
1. Build the examples named in `agent_docs/examples/README.md` and compare the results with each `expected.md`.
2. Inspect `/`, `/works`, and one work page.
3. Review the examples as an accepted source layout, including the created-date shape and named-section layout they use.
