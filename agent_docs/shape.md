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
1. The author adds each work as one named `.md` or `.html` file under `works/` or under a section folder in `works/`. A work may use its own folder when it needs local assets or legacy metadata.
2. Adding a work file or work folder there is enough to make it part of the site.
3. The author lists sections as `###` headings under the single `##` contents heading in `home.md`, in the order they should appear in the home-page contents index. Text beneath a section heading defines the home-page shelf description.
4. A work belongs to a home-page section when its parent folder under `works/` matches that section name, ignoring case and treating spaces, underscores, and hyphens as the same. Works directly under `works/` or under an unmatched section folder go to `Other works`.
5. Each work derives its title and published path from its file stem or folder name. The home-page contents index uses the title as the entry label and the slashless path as the reference label.
6. Publish each work at `/<slug>`.
7. A Markdown work body is parsed as CommonMark, with wikilinks as a Labyrinth inline feature. A work can also be authored as an HTML body fragment.
8. People using the site get a cover page at `/`, one work page for each work, `/feed.xml`, and a `/write` page when `home.md` defines a Tally link.
9. The home page places the site contents index below the cover.
10. Every page except the Atom feed uses the shared site frame.
11. Put work-page navigation in a left-side rail on wide screens and after the work on narrow screens.
12. Build one shared site navigation from the home contents link and the authored homepage links. On the home page, place it in the cover so it starts large, resolves to compact navigation on scroll, and fades before the contents section reaches it. On work and utility pages, put compact navigation in normal document flow so it reserves space and scrolls with the page. Route a Tally `home.md` link through the generated `/write` page.
13. Put the site title in the shared top line on every shared-frame page, and make that title link to the home page on every shared-frame page including the home page itself. Show the authored home cover text as subtitle metadata on the home page only.
14. Build the home-page contents index and the work-page site contents groups from one section-and-work list.
15. On wide work pages, put the current section label and that section's works in the left rail. Link the section label to its matching home-page contents section. Nest the current-work heading index under the current work entry.
16. On narrow work pages, put the current-work heading index in a collapsed `Contents` block after the title. Put a centered up-arrow link to the work top and the right-aligned publish date directly after the work body and backlinks. Then show the other current-section works as home contents rows.
17. Show only the current section in work-page navigation.
18. Show every named section on the home page even when no works resolve there. Show `Other works` only when at least one work falls back there.
19. Use row entries in the home-page contents index. Pair each work title with a baseline dotted leader and the slashless path reference aligned at the right. Do not show publish dates there.
20. Keep the work body and backlinks in one page body.
21. Site navigation links are plain links. Feed and contact content live on `/feed.xml` and `/write` rather than in hover panels.
22. Embed the Tally form on `/write` so site navigation remains available around the form.
23. Put the site title and Read, Follow, and Write heading links in the browser-facing feed guide.
24. The shared `Read` link targets the home-page contents section and lands with the compact home navigation still visible at the top.

## Micro-Features
- `Heading self-links`: Give each body heading an id from its visible text. Link the heading text to that id.
- `Content nav sidebar`: Two or more top-level body headings add current-work links under the current work entry in the wide-screen left rail and in the narrow-screen collapsed `Contents` block. The current target marks the matching entry there. Without a target, the first entry is current.
- `wikilinks`: A `[[...]]` link is a soft reference to a work. Match against the work title, slug, and any aliases in work metadata. Ignore case and treat spaces, underscores, and hyphens as the same. Link matches to the work's published path. Use the label as the visible text when present. Render plain text for misses.
- `Backlinks`: A work-to-work link adds the source work title to a backlinks section on the destination work page. The backlinks section appears after the body content.

## Acceptance Checks
1. Build the examples named in `agent_docs/examples/README.md` and compare the results with each `expected.md`.
2. Inspect `/` and one work page.
