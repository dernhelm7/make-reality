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
2. One visual system spans the cover page, the contents, and the reading page.
3. Use a left-side navigation rail on work pages, restrained page heads, and a continuous page field.
4. Let type, spacing, and hierarchy carry most of the visual work. Keep ornament minimal.
5. Use `#ffffff` for the page, `#202020` for the stronger text, `#3a3a3a` for softer text, and `#0a7c80` as the accent.
6. Use ET Book, self-hosted, as the main face. A secondary face may label dates and navigation.
7. Use one fluid `7/6` ladder for text, leading, and major spacing. Express it with `rem`, `em`, `ch`, `%`, `vh`, or `vw`. Do not set the root font size or use `px`.
8. Use a title-page cover on the home page: left-aligned title, a separate cover line beneath it, generous top spacing, an empty left gutter, global links beneath the cover header, and one home-column measure for the cover header and `Contents`.
9. Keep the visible `Contents` section below the first screen on narrow and wide layouts.
10. Set the home-page section descriptions as short running-text subheads beneath each shelf title.
11. Use open dotted leaders in the home-page `Contents` rows. Space the dots far enough apart that each dot reads as a mark.
12. Use a Tufte-style reading layout on work pages: narrow body column, semantic width bounds for the rail and body, a date-width margin-note track, title-only page head, publish date in the top of the margin-note track aligned with the rail header row, current section label in the left rail, current-work index nested under the current work entry, and gutters that widen before the body column widens.
13. Use interval-derived running-text leading and generous section spacing.
14. Anchor the work-page rail to the page gutter. Match its top inset to that gutter.
15. Set the desktop utility links at the same inset from the bottom-left corner as from the left edge.
16. Use one sans-serif face throughout the navigation rail.
17. Use the back-link text size for work names and current-work outline items in the navigation rail.
18. Use a faint guide line for nested current-work headings and a spaced dot for the current entry. Anchor the dot to the line box with font-relative units.
19. Remove underlines from heading self-links and nested current-work heading links. Keep the nested current-work heading spacing tight.
20. Use accent color and the external-link marker to signal body links. Do not use a heavy underline stroke.
21. Reserve accent hover color in the rail for links that change pages.
22. Use semantic-only labels for link groups when spacing and typography already define their role.
23. On narrow screens, restack the work-page rail before the reading layout. When the reading layout restacks, keep the current-work index nested with the current work entry, move sidenotes inline or beneath their paragraph, and fit images and audio controls to the available width.
24. Let images flow unframed with the page.
25. Keep motion light and use CSS or inline SVG only. Use a semi-transparent outlined circle for link cursors.

## Acceptance Checks
1. Review the page-shape fixtures named in `agent_docs/examples/README.md` on desktop and mobile.
2. Inspect the reading-layout fixture named in `agent_docs/examples/README.md` in wide and narrow layouts.
3. Inspect the generated stylesheet for the visual anchors in this document.
