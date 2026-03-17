# Build

## 1. Purpose
This document defines how the site is built.

## 2. Decisions Owned
- The build stack
- Required source inputs
- Output location and structure
- Discovery, rendering, and copying steps
- Validation behavior and build errors

## 3. Requirements

### 3.1 Build Stack
1. The site is built with Python as a local file-based build.
2. The build produces plain static files in `dist/`.

### 3.2 Required Inputs
1. The build reads `site.toml` from the site root.
2. The build reads the `works/` directory from the site root.
3. The build treats every direct child folder of `works/` as one candidate work.

### 3.3 Build Flow
1. The build loads and validates `site.toml`, then discovers work folders under `works/`.
2. For each work, the build validates its source files, loads `meta.toml`, and resolves metadata and derived defaults using `bones.md`.
3. For each work, the build turns the main source file into work body content:
   - `index.md` is converted to HTML with a CommonMark-compatible renderer. Raw HTML is disabled, wikilinks are resolved, and body headings are demoted so the Markdown body starts at `h2`.
   - `index.html` is read as authored work body content. If it contains a `<body>`, the build uses only that body's contents. If it discards non-empty content outside the body, it warns.
4. The build renders the homepage, the works index, each work page, and `/feed.xml`.
5. Feed items are written newest first and include the title, canonical URL, GUID equal to that URL, summary when one is present, and the created timestamp converted to the standard RSS 2.0 date format for `pubDate`.
6. The build copies local work assets with relative paths preserved and includes `work.css` only on its own work page.

### 3.4 Index Generation
1. The build generates `/works` using the section, fallback, sorting, and entry rules in `shape.md` and `bones.md`.

### 3.5 Validation And Errors
1. The build stops with a clear error when `site.toml` is missing, malformed, or missing required fields.
2. The build stops with a clear error when `site.toml.url` is not an absolute URL or ends with a trailing slash.
3. The build stops with a clear error when two works resolve to the same slug.
4. The build stops with a clear error when a work contains both `index.md` and `index.html`, or neither of them.
5. The build stops with a clear error when a work is missing `meta.toml`.
6. The build stops with a clear error when `created` is missing or does not match the timestamp type defined in `bones.md`.
7. The build rejects custom HTML that contains script tags or inline event-handler attributes.
8. The build stops with a clear error when a work slug collides with a reserved top-level path owned by the site, including `works`.

### 3.6 Output Contract
1. The generated output contains only static HTML, CSS, images, audio files, and other copied assets. It includes no JavaScript.
2. The generated output is deterministic for unchanged source input.
3. Every internal link emitted by the build points to a generated page or copied asset.
4. The canonical public URLs for the works index and work pages are slashless: `/works` and `/<slug>`.
5. The build constructs absolute canonical URLs by joining `site.toml.url` with `/`, `/works`, and `/<slug>`.
6. The build writes the homepage to `dist/index.html`, the works index to `dist/works/index.html`, each work page to `dist/<slug>/index.html`, and the feed to `dist/feed.xml`.

## 4. Acceptance Checks
1. Run the build with a valid `site.toml`, one Markdown work, and one HTML work and confirm that it writes `dist/index.html`, `dist/works/index.html`, `dist/<slug>/index.html`, and `dist/feed.xml`.
2. Add a work with `meta.toml` containing only `created` and confirm that the build derives title and uses the created timestamp format defined in `bones.md`.
3. Add a work with no `created` and confirm that the build fails with an instruction to set `created` in `meta.toml`.
4. Add configured and unknown section ids and confirm that `/works` matches the section, fallback, sorting, and entry rules in `shape.md` and `bones.md`.
5. Add local images, audio files, and `work.css` to a work and confirm that the build copies or includes them correctly.
6. Add a Markdown work whose source starts with `# Heading` and confirm that the page keeps the work title as `h1` and renders the body heading at `h2`.
7. Add a Markdown work with one existing wikilink and one missing wikilink and confirm that the output rewrites one and leaves the other as plain text.
8. Confirm that `/feed.xml` lists works newest first, uses the canonical work URL as both link and GUID, and converts `created` to the standard RSS 2.0 date format for `pubDate`.
9. Add custom HTML with a `<body>` and non-empty content outside it and confirm that the build uses only the body's contents and warns that the outside content was discarded.
10. Add invalid inputs for each validation rule in `3.5` and confirm that the build fails with clear messages.
11. Confirm that the generated output contains no JavaScript.

## 5. Open Questions
None.
