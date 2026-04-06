# Look

## Purpose
Specify how the site looks.

## Decisions Owned
- The overall visual direction
- The visual anchors
- The reading layout
- How the layout restacks on narrow screens
- How media and motion fit into it

## Requirements
1. The site feels closer to a printed book or small press publication than to a blog or app.
2. One visual system carries the reader from the cover page to the table of contents to the reading page. Type, spacing, and hierarchy do most of the work. Ornament is minimal.
3. That system uses `#fffff8` for the page, `#1c1a17` for body text, and `#0a7c80` as the accent.
4. ET Book, self-hosted, is the main face. A secondary face may be used for labels, dates, and the global links block.
5. Size and layout stay fluid. Use `rem`, `em`, `ch`, `%`, `vh`, or `vw`. Do not set the root font size or use `px`.
6. The cover page keeps a left-aligned title-page rhythm with generous top spacing.
7. Work pages use a Tufte-style reading layout: a narrow body column, a left-side section index when present, and a sidenote margin.
8. Body line-height is `1.5`. Major sections use generous spacing. The global links block stays compact and consistent as readers move through the site.
9. On narrow screens, the reading layout restacks without horizontal scrolling. The section index moves above the body, sidenotes move inline or beneath their paragraph, and images and audio controls fit the available width.
10. Images are unframed and flow with the page.
11. Motion, if used, stays light and uses CSS or inline SVG only. The cursor on links is a semi-transparent outlined circle.

## Acceptance Checks
1. Review the page-shape fixtures named in `agent_docs/examples/README.md` on desktop and mobile.
2. Inspect the reading-layout fixture named in `agent_docs/examples/README.md` in wide and narrow layouts.
3. Inspect the generated stylesheet for the visual anchors in this document.
