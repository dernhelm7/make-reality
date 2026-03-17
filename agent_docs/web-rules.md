# Web Rules

## 1. Purpose
This document defines the web standards the site must meet in its generated output.

## 2. Decisions Owned
- HTML semantics and landmark structure
- Keyboard and focus behavior
- Responsive and reduced-motion behavior
- Progressive enhancement requirements
- Interoperability rules for media, URLs, and indie-web markup

## 3. Requirements

### 3.1 Markup
1. Every public page is a valid HTML5 document with a declared document language.
2. Every public page uses semantic landmarks, including `header`, `main`, and `footer`.
3. Every public page contains one `main` landmark only.
4. Pages use heading levels in order, starting with one page-level heading.
5. The works index uses list markup for work entries.
6. Dates are rendered with a machine-readable `datetime` value in the timestamp type defined in `bones.md`, inside a `time` element.
7. Figures, captions, quotations, and audio players use their native HTML elements when those content types appear.
8. The site's global links block is exposed as navigation markup.

### 3.2 Accessibility
1. Every interactive element is reachable and usable with a keyboard alone.
2. Focus is always visible and visually distinct from surrounding text.
3. The layout remains readable at `320px` wide and at `200%` browser zoom without loss of content or function.
4. Link text describes the destination or action in plain language.
5. Informative images include alternative text in the rendered markup. Decorative images use empty alternative text.
6. Audio uses visible native controls and never starts automatically.
7. Motion, if present, is subtle and respects the user's reduced-motion preference.
8. If the global links block reveals extra detail in a compact state, that detail is also available on keyboard focus or activation.

### 3.3 Progressive Enhancement
1. Reading, the site's global links block, image viewing, and audio playback work when scripting is unavailable.
2. The generated site includes no JavaScript.
3. The site does not depend on client-side routing, client-side rendering, or custom widgets to expose core content.

### 3.4 Interoperability
1. The site keeps public URLs stable for unchanged content across rebuilds.
2. The homepage exposes an `h-card`.
3. The homepage `h-card` maps the site title to `p-name`, the homepage canonical URL to `u-url`, and the site statement to `p-note`.
4. Contact links and gift links stay as normal links. A `mailto:` contact link may also use `u-email`.
5. Every work page exposes an `h-entry`.
6. The work page `h-entry` maps the resolved title to `p-name`, the canonical URL to `u-url`, the created timestamp to `dt-published`, the summary to `p-summary` when one is present, and the main body content to `e-content`.
7. Every work page declares its own canonical URL as canonical.
8. The homepage exposes a discoverable RSS feed link.
9. Internal links resolve correctly on a plain static host.

## 4. Acceptance Checks
1. Validate the generated pages as HTML5 documents.
2. Navigate every page with the keyboard and confirm that all links and audio controls work, and that any extra detail in a compact global links block is available on focus or activation.
3. Open the site with scripting disabled and confirm that reading, the site's global links block, and audio playback still work.
4. Resize to `320px` width and zoom to `200%` and confirm that content remains readable and usable.
5. Inspect the homepage and confirm that its `h-card` matches the required mapping.
6. Inspect a work page and confirm that its `h-entry` matches the required mapping.
7. Inspect a work page and confirm that it includes a canonical self-link.
8. Inspect the homepage and confirm that it exposes a discoverable RSS feed link.
9. Confirm that the generated output contains no JavaScript files, inline scripts, or script tags.

## 5. Open Questions
None.
