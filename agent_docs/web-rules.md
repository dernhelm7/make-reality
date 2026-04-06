# Web Rules

## Purpose
This document says what the built site gives the browser.

## Decisions Owned
- What the browser gets
- What the reader can do without scripting
- What other systems can discover

## Requirements
1. The site gives the browser valid, semantic HTML and the usual page metadata.
2. The site gives readers accessible pages.
3. Readers can read and move through the site without scripting.
4. The site exposes its canonical URL and the metadata it needs for identity and feed discovery.

## Acceptance Checks
1. Build the web-output examples and check them with HTML validation, keyboard-only navigation, scripting disabled, and a narrow viewport.
2. Inspect `/`, `/works`, and one work page for canonical and feed metadata.
