# Shape

## 1. Purpose
This document defines the user experience shape of the site.

## 2. Decisions Owned
- The public page set
- The content order on each page type
- The site's global links block
- The structure and ordering of the works index
- The layout frame for work pages

## 3. Requirements

### 3.1 Public Pages
1. The site publishes exactly three page types: `/`, `/works`, and `/<slug>`.
2. The homepage acts as the cover and title page of the site.
3. The works index acts as the table of contents for the site.
4. Each work page presents one work within the site's layout frame.
5. The site also publishes one non-HTML feed output at `/feed.xml`.

### 3.2 Global Links Block
1. Every page includes the same global links block.
2. The global links block contains a link to `/works`, plus the configured contact links and gift links.
3. The global links block may use different presentation variants by page type, but it keeps the same destination set everywhere.
4. The current location is apparent from the page structure and global links block treatment.

### 3.3 Homepage
1. The homepage main content contains only the site title, short statement, and a clear link to `/works`.

### 3.4 Works Index
1. The works index uses the section order from `site.toml`.
2. Works with no section, or with an unknown section id, appear in a final fallback section named `Other works`.
3. Works are sorted newest first within each section. Ties are sorted by slug in ascending order.
4. Each work entry links to `/<slug>` and shows its index label, creation date, and summary when one is present.

### 3.5 Work Pages
1. Every work page uses the same layout frame.
2. The work page presents a work header before the body content.
3. The work header includes the resolved title as the page-level heading, plus the creation date and summary when one is present.
4. The main reading area contains either converted Markdown or authored HTML body content.

## 4. Acceptance Checks
1. Confirm that the spec defines only `/`, `/works`, and `/<slug>`.
2. Confirm that the spec also defines a feed output at `/feed.xml`.
3. Confirm that the homepage main content contains only the title-page content described in this document.
4. Confirm that `/works` uses configured section order, appends `Other works` last, and places works without section metadata there.
5. Confirm that `/`, `/works`, and `/<slug>` all include the global links block.
6. Confirm that a work page includes a work header and body content.
7. Confirm that the work header owns the page-level heading.
8. Confirm that Markdown works and HTML works use the same layout frame.

## 5. Open Questions
None.
