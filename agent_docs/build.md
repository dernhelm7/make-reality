# Build

## Purpose
Specify how to generate the static site from source files.

## Decisions Owned
- What the author runs
- What the build reads
- Where the build writes
- What the build publishes
- What the build validates
- What the build says when it fails

## Source Model
- The local build command is `./build-site [--build-url <url>] <site-root> <publish-root>`.
- That command resolves the local `labyrinth` package from the repo itself. Calling it by path does not require the current shell directory to be the repo root.
- The repo may define a GitHub Pages workflow. That workflow builds `site/` to `public/` with `./build-site`.
- The site root contains `site.toml`, `home.md`, `feed.md`, and may contain `works/`.
- `site.toml` defines `url`, `lang`, `title`, `statement`, `author_name`, and `updated`.
- `home.md` defines the homepage title, cover text, homepage links, contents heading, and contents section labels and descriptions.
- `feed.md` defines the browser-facing feed guide. The build replaces `{feed_url}` with the current feed URL.
- `site.toml` `url` is the canonical site URL.
- `home.md` section headings define the section names that work `section` values may target.
- A `home.md` link to `https://tally.so/r/<id>` is the source for the matching Tally form panel.
- A `home.md` link to `/feed.xml` is the source for a feed preview panel built from the body paragraphs in `feed.md`, clipped inside the fixed panel and followed by a visible `Follow` link to `/feed.xml`.
- The home page may include the inline event handler that switches those preview panels. It attaches only to the home-page global links.
- `--build-url` sets the output base URL for one build.
- The public HTML uses relative links for pages and assets.
- The public HTML sets a page base URL from the current build URL and the current public path.
- The public HTML uses line breaks and indentation.
- The build uses `site.toml` `url` for canonical URLs and Atom feed IDs.
- The build uses the current build URL for feed self links, feed alternate links, and absolute URLs inside feed entry content.
- The Atom feed includes XHTML extension markup for a browser-facing subscription guide, a home link, and visible linked entry URLs.
- The browser-facing feed view is produced by an XSL stylesheet so mobile browsers receive an HTML viewport.
- Each work folder contains `meta.toml` and exactly one body file: `index.md` or `body.html`.
- `meta.toml` requires `created`, `updated`, and `atom_id`. It may also define `section` and `aliases`.

## Requirements
1. The project defines one local build command at `./build-site`.
2. That command reads one site root from `site.toml`, `home.md`, `feed.md`, and `works/`.
3. That command writes one publish root and removes stale published files from it.
4. The publish root contains public pages, `/feed.xml`, `/feed.xsl`, `/feed.css`, `/site.css`, shared public assets such as self-hosted fonts, and no generated JavaScript assets or dependencies.
5. The publish root leaves out source-only files and build-only files.
6. The build validates the required source fields, duplicate published paths, and broken explicit internal links written by the author. Unmatched wikilinks do not fail the build.
7. The same site root and build URL produce the same publish root and public paths.
8. On failure, the build stops and reports the file and rule that caused the failure.
9. If the repo defines a GitHub Pages workflow, that workflow publishes the built `public/` root from the same build logic as the local command.
10. The build writes Atom 1.0 at `/feed.xml`.
11. The build links `/feed.xml` to `/feed.xsl` through `<?xml-stylesheet ...?>`; the transform renders the browser-facing feed as HTML and loads `/feed.css`.
12. The build writes line-broken, indented XML for `/feed.xml`.
13. The host serves `/feed.xml` as XML, not `application/atom+xml`. Prefer `application/xml; charset=utf-8`.

## Acceptance Checks
1. Run `./build-site <site-root> <publish-root>` against the full-output examples and inspect the publish root against the behavior named in each `expected.md`.
2. Build one unchanged example twice and compare the publish roots.
3. Run the named validation cases for build failures in `agent_docs/examples/validation-severity.md`.
