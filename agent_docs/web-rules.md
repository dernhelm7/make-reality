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
1. The site gives the browser valid, semantic HTML.
2. Every public HTML page uses semantic landmarks.
3. The site gives readers accessible pages.
4. Every interactive element is reachable and usable with a keyboard alone.
5. Focus is always visible and visually distinct from surrounding text.
6. Link text names the destination or action in plain language.
7. External links stay visibly distinct from internal work links without relying on color alone.
8. Readers can read and move through the site without scripting.
9. Public URLs stay stable for unchanged content across rebuilds.
10. Each work page exposes an `h-entry` for the work title, canonical URL, and main body content.
11. Published pages expose canonical URLs, and the homepage exposes feed discovery metadata.

## Acceptance Checks
1. Build the web-output examples and check them with HTML validation, keyboard-only navigation, scripting disabled, and a narrow viewport.
2. Inspect `/`, `/works`, and one work page for semantic landmarks, canonical metadata, and feed discovery metadata.
3. Inspect one work page for the `h-entry` mapping.
4. Inspect `reading-microfeatures` for link treatment.
5. Build one unchanged example twice and confirm that its public URLs do not change.
