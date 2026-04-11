# Web Rules

## Purpose
Specify accessibility and interoperability rules.

## Decisions Owned
- Semantic HTML for published pages
- No-script reading and navigation
- Keyboard and focus behavior
- Link usability and distinction
- Stable public URLs and machine-readable discovery

## Requirements
1. Published pages are valid, semantic HTML.
2. Every public HTML page uses semantic landmarks.
3. Every interactive element is reachable and usable with a keyboard alone.
4. Focus is always visible and visually distinct from surrounding text.
5. Link text names the destination or action in plain language.
6. Mark external links with an appended marker.
7. Readers can read and move through the site without scripting.
8. Public URLs stay stable for unchanged content across rebuilds.
9. Each work page exposes an `h-entry` for the work title, canonical URL, and main body content.
10. Published pages expose canonical URLs, and the homepage exposes feed discovery metadata.

## Acceptance Checks
1. Build the `web-output fixtures` named in `agent_docs/examples/README.md`.
2. Check those fixtures with HTML validation, keyboard-only navigation, scripting disabled, and a narrow viewport.
3. Verify the features in this doc against the corresponding generated pages, `expected.md`, and named validation cases.
4. Build one unchanged example twice and compare its public URLs.
