# Web Rules

## 1. Purpose
This document defines the web standards the site must meet in its generated output.

## 2. Decisions Owned
- HTML semantics and document metadata
- Keyboard and focus behavior
- Responsive and reduced-motion behavior
- Progressive enhancement requirements
- Interoperability rules for media, URLs, and indie-web markup

## 3. Requirements

### 3.1 Document Contract
1. Every public HTML page is a valid HTML5 document with the document language set from the resolved site record defined in `bones.md`.
2. Every public HTML page uses semantic landmarks (`header`, `main`, `footer`), with exactly one `main`.
3. Pages use heading levels in order, starting with one page-level heading.
4. The site's global links block is exposed as navigation markup.
5. The works index uses list markup for work entries.
6. Dates are rendered with a machine-readable `datetime` value in the timestamp type defined in `bones.md`, inside a `time` element.
7. Figures, captions, quotations, and audio players use their native HTML elements when those content types appear.
8. The HTML `title` element uses the resolved site title on `/`, `Works | {resolved site title}` on `/works`, and `{resolved work title} | {resolved site title}` on work pages.
9. Every public HTML page declares its own canonical URL as canonical.
10. The `/works` link uses `aria-current="page"` on `/works` and omits `aria-current` on `/` and work pages.

### 3.2 Accessibility
1. Every interactive element is reachable and usable with a keyboard alone.
2. Focus is always visible and visually distinct from surrounding text.
3. The layout remains readable at `320px` wide and at `200%` browser zoom without loss of content or function.
4. Link text describes the destination or action in plain language.
5. Informative images include alternative text in the rendered markup. Decorative images use empty alternative text.
6. Audio uses visible native controls and never starts automatically.
7. Motion, if present, is subtle and respects the user's reduced-motion preference.

### 3.3 Progressive Enhancement
1. Reading, the site's global links block, image viewing, and audio playback work when scripting is unavailable.
2. The shared site output includes no build-generated JavaScript and does not depend on client-side routing, client-side rendering, or custom widgets to expose core content. A work page may include explicit author-provided JavaScript in `index.html`.
3. Site styling works from the shared site stylesheet without relying on scripting.

### 3.4 Interoperability
1. The site keeps public URLs stable for unchanged content across rebuilds.
2. The homepage exposes an `h-card` mapping: resolved site title to `p-name`, homepage canonical URL to `u-url`, and resolved site statement to `p-note`. Contact links and gift links stay as normal links. A `mailto:` contact link may also use `u-email`.
3. Every work page exposes an `h-entry` mapping: resolved title to `p-name`, resolved work canonical URL to `u-url`, created timestamp to `dt-published`, summary to `p-summary` when one is present, and the main body content to `e-content`.
4. The homepage includes `<link rel="alternate" type="application/rss+xml" href="/feed.xml">`.
5. Internal links resolve correctly on a plain static host.

## 4. Acceptance Checks
1. Build `agent_docs/examples/minimal-markdown` and `agent_docs/examples/html-work`, then validate the generated output against the requirements in this document with HTML validation, keyboard-only navigation, scripting disabled, and a narrow viewport.
2. Inspect `/`, `/works`, and one work page from those examples and confirm that the required microformat mappings, canonical link, and RSS feed link are present.

## 5. Open Questions
None.
