# Build

## 1. Purpose
This document defines the build pipeline that turns the source model into the published site.

## 2. Decisions Owned
- The build stack
- The pipeline order
- Work body rendering rules
- Feed and asset copying rules
- Output location and structure
- Validation behavior and build errors

## 3. Requirements

### 3.1 Build Stack And Inputs
1. The site is built with Python as a local file-based build and produces plain static files in `dist/`.
2. The implementation root contains `build.py` as the build entry point and `requirements.txt` as the Python dependency manifest. `requirements.txt` may be empty.
3. The dependency install command is `python -m pip install -r requirements.txt`.
4. The canonical build command is `python build.py [site-root] [output-root]`.
5. When `site-root` is omitted, the build reads from the current working directory. When `output-root` is omitted, the build writes to `dist/` under that site root.
6. The build uses the source model defined in `bones.md`.
7. The build reads `site.toml` and the direct children of `works/` from the site root.

### 3.2 Build Flow
1. The build loads and validates `site.toml`, discovers candidate work folders under `works/`, and resolves the site record and work records defined in `bones.md`.
2. The build recreates `dist/` on each run before writing new output.
3. The build renders each work body from its main source file.
4. For each work, the build determines which files the work body references in the same work folder.
5. The build renders the homepage from the resolved site record and the page shape defined in `shape.md`.
6. The build renders the works index from the resolved site record, the resolved work records, and the page shape defined in `shape.md`.
7. The build renders each work page from one resolved work record and its rendered body.
8. The build renders `/feed.xml` from the resolved site record and the resolved work records.
9. The build copies those referenced local files with relative paths preserved.
10. The build validates generated output against this document and `web-rules.md`.

### 3.3 Work Body Rendering
1. `index.md` uses CommonMark. No Markdown extensions are supported except the wikilinks defined in `bones.md`. If renderer behavior is unclear, `agent_docs/examples/` defines the expected output. Raw HTML is disabled, wikilinks are resolved, and body headings are demoted so the Markdown body starts at `h2`.
2. `index.html` is read for body content, discarding the rest. Author-provided JavaScript may remain when it is part of that authored body.
3. The build writes the shared site stylesheet to `dist/site.css` and links every public HTML page to `/site.css`.
4. When `work.css` is present for a work, the build emits it inline on the final work page after the shared site stylesheet so it overrides shared CSS.

### 3.4 Feed Generation
1. The feed channel uses the resolved site record for `title`, `link`, and `description`.
2. Feed items are written newest first. Each item includes the resolved work title, the resolved work canonical URL, GUID equal to that URL, `pubDate` converted from the created timestamp to the standard RSS 2.0 date format, and `description` set to the summary when one is present and omitted otherwise.

### 3.5 Output Contract
1. The generated output contains static HTML, CSS, images, audio files, and other copied assets.
2. The generated output is deterministic for unchanged source input.
3. The generated output contains only files for the current source input.
4. Every internal link emitted by the build points to a generated page or copied asset.
5. Canonical public URLs are slashless: `/`, `/works`, and `/<slug>`. The build constructs absolute canonical URLs by joining the resolved site canonical URL with those paths.
6. Output paths are `dist/index.html`, `dist/works/index.html`, `dist/<slug>/index.html`, `dist/feed.xml`, and `dist/site.css`.
7. The deployed site serves the canonical public URLs defined in this spec. Deployment-specific routing is outside the build contract.
8. The build publishes referenced local asset files and does not publish unreferenced local files.
9. The build does not publish `meta.toml`, `index.md`, `index.html`, or `work.css` as copied files.

### 3.6 Validation And Errors
1. Validation uses two outcomes: `fatal` and `recoverable`.
2. A `fatal` issue stops the build cleanly and writes no new output.
3. A `recoverable` issue reports clear actionable detail, keeps the build running, and writes inspectable output for the affected artifact when possible.
4. These issues are `fatal`: missing or malformed `site.toml`; missing required `site.toml` fields; invalid `site.toml.url`; duplicate section numbers; invalid work slug; missing `meta.toml`; both or neither main source files; missing or invalid `created`.
5. These issues are `recoverable`: a referenced local asset missing from a work folder; a generated page, feed, or stylesheet that violates a requirement in `web-rules.md` while the build can still write the affected output for inspection.
6. The build validates source input against `bones.md` and generated output against `web-rules.md` and this document.
7. The build reports `fatal` and `recoverable` issues clearly and prominently, with actionable detail. It may report derived defaults and fallback placements as informational output.
8. The build exits with status code `0` when it succeeds without `fatal` or `recoverable` issues.
9. The build exits with status code `1` when one or more `recoverable` issues occur, even if it writes inspectable output.
10. The build exits with status code `2` when a `fatal` issue occurs.

## 4. Acceptance Checks
1. Install dependencies with `python -m pip install -r requirements.txt`, then build `agent_docs/examples/minimal-markdown`, `agent_docs/examples/html-work`, and `agent_docs/examples/wikilinks-and-assets` with `python build.py [site-root] [output-root]`, and confirm that each output matches its `expected.md`, including `/`, `/works`, work pages, `/feed.xml`, `site.css`, and referenced local assets only.
2. Build `agent_docs/examples/minimal-markdown` twice with unchanged input and confirm deterministic output.
3. Remove or rename a referenced local asset in `agent_docs/examples/wikilinks-and-assets`, build again, and confirm the behavior matches the `recoverable` rule in `agent_docs/examples/validation-severity.md`.
4. Run the `recoverable` cases in `agent_docs/examples/validation-severity.md` and confirm that the build finishes, reports them clearly, and writes inspectable output.
5. Run the `fatal` cases in `agent_docs/examples/validation-severity.md` and confirm that the build stops cleanly without writing new output.
6. Confirm that a successful build exits `0`, a `recoverable` build exits `1`, and a `fatal` build exits `2`.

## 5. Open Questions
None.
