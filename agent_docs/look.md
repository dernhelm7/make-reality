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
5. Do not use horizontal hairlines or rule dividers. Separate regions with spacing, type, and structure.
6. Use `#ffffff` for the default page, `#202020` for the stronger text, and `#3a3a3a` for softer text. Take the contrast accent from `site.toml` `primary_color`, defaulting to `#110411`, and derive soft accents, dark-mode colors, and feed code-surface colors from shared primary-color tokens rather than component overrides. Set dark-mode ink as a softened off-white so light text does not bloom against the dark page.
7. Use ET Book, self-hosted, as the body face. Use Basteleur, self-hosted, for display titles and headings. A secondary face may label dates and navigation.
8. Use one fluid `7/6` ladder for text, leading, and major spacing. Express it with `rem`, `em`, `ch`, `%`, `vh`, or `vw`. Do not set the root font size or use `px`.
9. Put the site title in the shared header line. Keep the title at the left, and set it at the same face and size as compact site navigation. On the home page, show the authored cover text as light centered subtitle metadata in the readable body face at the compact site-navigation size; do not show that subtitle on work or utility pages.
10. Keep the home cover above the contents index. Keep the contents section addressable at `#contents` for the site navigation, and give it at least one viewport of height so it reads as its own page even when the index is short.
11. Stack the home-page contents sections in source order as one vertical column with generous vertical space between sections. On wide screens, set each shelf as a left metadata track with the title and short running-text description and a right entries track with the work rows; use generous column space, align the first work-link text optically with the sticky heading during ordinary scrolling, and make section links land in that same alignment state. Give the contents area enough end space for the final shelf to reach the sticky inset. Set shelf titles in regular text visibly larger than work row labels, and set home work row labels and shelf descriptions large enough to read as running text with proportional space between rows.
12. Treat shelf headings as static labels unless the markup makes them links.
13. Place the home-page site navigation links in the lower half of the cover, centered across the page, set in the display face at the home title scale. As the links approach the shared top inset, shrink and tighten them into compact top navigation so the docked position and final compact size arrive together. Keep the compact nav visible as the contents header, and make direct navigation to `#contents` load at that compact state without smooth-scroll shrink motion. Then use a slow-start fade that finishes when the first contents line is one normal body-text ink gap below it. On work and utility pages, place compact navigation at the top of the document in normal page flow so it scrolls with the page. On wide work pages, keep the site title pinned at the shared top inset while the compact navigation scrolls. Set the links near the ink color and fade them slightly lighter on hover or focus. Put a centered bullet between links, set from the display face and sized close to the custom cursor rather than as small punctuation. Do not use hover preview panels for feed or contact links.
14. Use baseline dotted leaders in the home-page contents rows. Put the work title at the left, the slashless path reference at the right, and let the dots fill the space between them. Keep home leaders smaller and tighter than work labels, and bound the title-to-leader and leader-to-reference gaps with one home row gap token so dots begin and end close to the adjacent text. Set the home row cadence from the text line box so multi-link shelves align with the description rhythm and read as one unit. Keep the slashless path reference in the link color.
15. Use a Tufte-style reading layout on work pages: narrow body column, semantic width bounds for the rail and body, a date-width margin-note track, title-only page head, publish date in the top of the margin-note track aligned with the rail header row, current section label in the left rail, current-work index nested under the current work entry, and gutters that widen before the body column widens.
16. Use interval-derived running-text leading and generous section spacing.
17. Anchor the work-page rail to the page gutter. Start the fixed rail below the shared header line at the same block position the in-flow rail would occupy, keep it fixed through the end of the page, and let the rail itself scroll only when its own content is taller than the viewport.
18. Set the desktop utility links at the same inset from the bottom-left corner as from the left edge.
19. Use one sans-serif face throughout the navigation rail.
20. Use the rail link text size for work names and current-work outline items in the navigation rail.
21. Use a faint guide line for nested current-work headings and an accent spaced dot for the current entry. Anchor the dot to the line box with font-relative units.
22. Remove underlines from heading self-links and nested current-work heading links. Keep the nested current-work heading spacing tight.
23. Use accent color and the external-link marker to signal body links. Do not use a heavy underline stroke.
24. Reserve accent hover color in the rail for links that change pages.
25. Use semantic-only labels for link groups when spacing and typography already define their role.
26. Put the site title on every shared-frame HTML page as small, muted header metadata in the same line as the compact site navigation.
27. On narrow screens, show the work title, collapsed `Contents` block, reading body, and backlinks before work-page end matter. Style the collapsed `Contents` summary with a compact arrow cue. Put a centered up-arrow link to the top of the work and the publish date right-aligned in one compact line directly after the work. Then show `More in {section}` as a muted section label with the other section works in the home contents row treatment. When the reading layout restacks, move sidenotes inline or beneath their paragraph, and fit images and audio controls to the available width.
28. Let images and inline diagrams flow unframed with the page and scale inside the reading column on narrow screens.
29. Present the feed with a light guide/header band over compact machine-readable rows on a dark code-like surface. Draw the light band from the site light-theme tokens and the dark rows from the site dark-theme tokens. Indent the feed guide and code rows from the same content inset. Keep the feed metadata and each entry on one scannable line with format-sized entry columns. Let code-like rows hang horizontally past narrow viewports rather than compressing or wrapping them.
30. Keep motion light and use CSS or inline SVG only. Use a semi-transparent outlined circle for link cursors.
31. Use a compact light/dark switch. Start from the reader's color-scheme preference, persist a manual choice for the current tab when scripting is available, and keep the switch working on the current page without scripting. Style it as a small fixed circular control aligned to the page inset, and drive the theme from shared color tokens. On `/write`, keep the Tally iframe transparent across site themes by setting the iframe color-scheme boundary deliberately.

## Acceptance Checks
1. Review the page-shape fixtures named in `agent_docs/examples/README.md` on desktop and mobile.
2. Inspect the reading-layout fixture named in `agent_docs/examples/README.md` in wide and narrow layouts.
3. Inspect the generated stylesheet for the visual anchors in this document.
