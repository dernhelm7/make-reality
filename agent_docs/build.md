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
- The local build command is `./build-site <site-root> <publish-root>`.
- That command resolves the local `labyrinth` package from the repo itself. Calling it by path does not require the current shell directory to be the repo root.
- The repo may define a GitHub Pages workflow. That workflow builds `site/` to `public/` with `python3 -m labyrinth build`.
- The site root contains `site.toml` and may contain `works/`.
- `site.toml` defines `url`, `lang`, `title`, `statement`, `contact_links`, `gift_links`, and `sections`.
- Each work folder contains `meta.toml` and exactly one body file: `index.md` or `body.html`.
- `meta.toml` requires `created`. It may also define `section` and `aliases`.

## Requirements
1. The project defines one local build command at `./build-site`.
2. That command reads one site root from `site.toml` and `works/`.
3. That command writes one publish root and removes stale published files from it.
4. The publish root contains public pages, `/feed.xml`, `/site.css`, shared public assets such as self-hosted fonts, and no build-generated JavaScript.
5. The publish root leaves out source-only files and build-only files.
6. The build validates the required source fields, duplicate published paths, and broken explicit internal links written by the author. Unmatched wikilinks do not fail the build.
7. The same site root produces the same publish root and public paths.
8. On failure, the build stops and reports the file and rule that caused the failure.
9. If the repo defines a GitHub Pages workflow, that workflow publishes the built `public/` root from the same build logic as the local command.

## Acceptance Checks
1. Run `./build-site <site-root> <publish-root>` against the full-output examples and inspect the publish root against each `expected.md`.
2. Build one unchanged example twice and compare the publish roots.
3. Run the named validation cases for build failures in `agent_docs/examples/validation-severity.md`.
