# Shape

## 1. Purpose
This document defines the site's public shape: one shared frame wrapped around three reading surfaces.

## 2. Decisions Owned
- The central public model
- The public route set
- The shared site frame
- The content order on each page type
- The structure and ordering of the works index

## 3. Requirements

### 3.1 Public Model
1. The site publishes one catalog of works inside one shared site frame, with three HTML page routes: `/`, `/works`, and `/<slug>`.
2. The homepage acts as the cover and title page for that catalog, and the works index acts as the table of contents.
3. `/<slug>` resolves one published work from the resolved work model defined in `bones.md`.
4. The site also publishes one non-HTML feed output at `/feed.xml`.

### 3.2 Shared Site Frame
1. Every HTML page uses the same site frame.
2. The site frame includes the global links block.
3. The global links block contains a link to `/works`, followed by the contact links and gift links from the resolved site record defined in `bones.md`.
4. The global links block may vary in presentation by page type, but it keeps the same destinations everywhere.
5. On `/works`, the `/works` link in the global links block is marked as the current page.

### 3.3 Homepage
1. The homepage main content contains only the site title and site statement from the resolved site record, plus a clear link to `/works`.

### 3.4 Works Index
1. The works index uses `Works` as the page-level heading.
2. The works index uses the section order from the resolved site record defined in `bones.md`.
3. Each section title on the works index uses `h2`.
4. The works index renders each work in the section placement from its resolved work record, including the final fallback section defined in `bones.md`.
5. Works are sorted newest first within each section. Ties are sorted by slug in ascending order.
6. Each work entry links to `/<slug>` and shows its index label, creation date, and summary when one is present.

### 3.5 Work Pages
1. Every work page uses the shared site frame and presents a work header before the body content.
2. The work header includes the resolved title as the page-level heading, plus the creation date and summary when one is present.
3. The main reading area contains either converted Markdown or authored HTML body content that starts at `h2` or lower.

## 4. Acceptance Checks
1. Build `agent_docs/examples/minimal-markdown` and `agent_docs/examples/metadata-overrides` and confirm that `/`, `/works`, and one work page use one shared frame and keep the global links destination set consistent.
2. Build `agent_docs/examples/section-fallback` and confirm that `/works` renders the configured sections in order and the fallback section from `bones.md` as the final section.

## 5. Open Questions
None.
