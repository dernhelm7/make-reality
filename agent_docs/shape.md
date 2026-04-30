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
3. The author lists sections as `###` headings under the single `##` contents heading in `home.md`, in the order they should appear in the home-page contents index. Text beneath a section heading defines the home-page shelf description.
4. A work may set `section` to one of those section names. Unnamed or unmatched works go to `Other works`.
5. Each work derives its title and published path from its folder name. The home-page contents index uses the title as the entry label and the slashless path as the reference label.
6. Publish each work at `/<folder-name>`.
7. A work can be written in Markdown or HTML body content.
8. People using the site get a cover page at `/`, one work page for each work, and `/feed.xml`.
9. The home page places the site contents index beneath the cover.
10. Every page except the Atom feed uses the shared site frame.
11. Put work-page navigation in a left-side rail.
12. Put the home-page global links block beneath the cover header in the main reading column.
13. Build the home-page contents index and the work-page site contents groups from one section-and-work list.
14. On work pages, put a back link, the current section label, and that section's works in the left rail. Nest the current-work heading index under the current work entry.
15. Show only the current section in that rail.
16. Show every named section on the home page even when no works resolve there. Show `Other works` only when at least one work falls back there.
17. Use row entries in the home-page contents index. Pair each work title with an open dotted leader. Do not show publish dates there.
18. Keep the work body and backlinks in one page body.
19. Home-page global links may reveal a preview panel. A Tally link reveals the same form. The feed link reveals an excerpt from `feed.md`. Entering or focusing a preview link changes the shown panel. Entering or focusing a normal global link clears it. Pointer exit does not change the panel.
20. The home-page contents heading links to the works index, not to itself.

## Micro-Features
- `Heading self-links`: Give each body heading an id from its visible text. Link the heading text to that id.
- `Content nav sidebar`: Two or more top-level body headings add current-work links under the current work entry in the left rail. The current target marks the matching entry there. Without a target, the first entry is current.
- `wikilinks`: A `[[...]]` link is a soft reference to a work. Match against the work title, folder name, and any aliases in `meta.toml`. Ignore case and treat spaces, underscores, and hyphens as the same. Link matches to the work's published path. Use the label as the visible text when present. Render plain text for misses.
- `Backlinks`: A work-to-work link adds the source work title to a backlinks section on the destination work page. The backlinks section appears after the body content.

## Acceptance Checks
1. Build the examples named in `agent_docs/examples/README.md` and compare the results with each `expected.md`.
2. Inspect `/` and one work page.
