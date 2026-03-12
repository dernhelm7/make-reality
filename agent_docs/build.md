# Build

This file defines how the approved spec turns into a working project: stack choice, project structure, CSS approach, commands, output location, and validation workflow.

## Stack

The launch site must use:

- Python 3 for the generator
- Markdown for work bodies
- plain CSS for styling
- static HTML output

## Inputs

The generator must read from these inputs:

- `content/site.toml`
- `content/works-index.toml`
- `content/works/*.md`
- `templates/base.html`
- `templates/home.html`
- `templates/works-index.html`
- `templates/work.html`
- `assets/site.css`
- `public/`

## Output Location

The generator must write the site to `dist/`.

The generated output must include:

- `dist/index.html`
- `dist/works/index.html`
- `dist/works/<slug>/index.html` for each work
- `dist/assets/site.css`
- copied files from `public/`

These outputs must cover every page and shared structure defined in `shape.md`.

## Commands

The build workflow must expose these commands:

- `python scripts/build.py` builds the site into `dist/`
- `python -m http.server --directory dist 8000` previews the generated site locally
- `python scripts/validate.py` validates content and output

## Project Structure

The implementation must organize the project with:

- content under `content/`
- templates under `templates/`
- styles under `assets/`
- generated output under `dist/`

## Validation Workflow

`python scripts/build.py` must fail when:

- required content fields are missing
- more than one work is marked `featured`
- no work is marked `featured`
- a works-index entry points to a missing work
- two works share the same slug

`python scripts/validate.py` must check:

- HTML output exists for every page defined in `shape.md`
- generated output contains no JavaScript files or script tags
- internal links resolve within `dist/`
