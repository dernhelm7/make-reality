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

## Requirements
1. The project defines one local build command.
2. That command reads one site root.
3. That command writes one publish root and removes stale published files from it.
4. The publish root contains only public site files: HTML pages, `/feed.xml`, one shared stylesheet, and no build-generated JavaScript.
5. The publish root leaves out source-only files and build-only files.
6. The build validates required content fields, duplicate published paths, and broken explicit internal links written by the author. Unmatched wikilinks do not fail the build.
7. The same site root produces the same publish root and public paths.
8. On failure, the build stops and reports the file and rule that caused the failure.

## Acceptance Checks
1. Run the documented build against the full-output examples and inspect the publish root against each `expected.md`.
2. Build one unchanged example twice and compare the publish roots.
3. Run the named validation cases for build failures in `agent_docs/examples/validation-severity.md`.
