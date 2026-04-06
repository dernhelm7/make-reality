# Build

## Purpose
This document says how site files become the published site.

## Decisions Owned
- How the build is run
- What the build publishes
- What the build says when it fails

## Requirements
1. The project has one documented local build command.
2. That command turns the site files into a plain static site.
3. The same input gives the same output and clears stale output.
4. The build publishes the files the site needs and leaves authoring files out.
5. When the build fails, it says why.

## Acceptance Checks
1. Run the documented build against the full-output examples and compare each result with its `expected.md`.
2. Build one unchanged example twice and confirm the output does not change.
