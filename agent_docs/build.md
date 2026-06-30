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
- The local shell launchers select Python 3.11 or newer before importing the `labyrinth` package.
- The repo may define a GitHub Pages workflow. That workflow builds `site/` to `public/` with `./build-site`.
- The site root contains `site.toml`, `home.md`, `feed.md`, and may contain `works/`.
- `site.toml` defines `url`, `lang`, `title`, `author_name`, and `updated`. It may define `statement` for generated description metadata and the Atom subtitle.
- `home.md` defines the homepage title, cover text, homepage links, contents link label, and contents section labels and descriptions.
- `feed.md` defines the browser-facing feed guide. The build replaces `{feed_url}` with the current feed URL.
- `site.toml` `url` is the canonical site URL.
- `home.md` section headings define the section names that section folders under `works/` may match.
- A `home.md` link to `https://tally.so/r/<id>` is the source for `/write`. The `/write` page preconnects to Tally, gives the iframe a direct eager source so the form starts loading with the page, and includes the Tally widget loader for enhancement.
- A `home.md` link to `/feed.xml` points readers to the browser-facing feed guide built from `feed.md`.
- `--build-url` sets the output base URL for one build.
- Local preview uses `./preview-site`, which passes `--build-url http://localhost:<port>` before serving the publish root and disables browser caching for preview responses so a rebuilt stylesheet is visible on reload.
- The public HTML uses relative links for pages and assets.
- The public HTML sets a page base URL from the current build URL and the current public path.
- The public HTML uses line breaks and indentation.
- HTML and CSS carry shared content, navigation, reading, and layout by default.
- While composing shared CSS, the build fills embedded SVG cursor RGB channels from the active light and dark page colors configured at the top of `labyrinth/style_sources/tokens.css`.
- Shared JavaScript, when present, is a small author-written inline snippet for one feature. It calls browser APIs directly, stays scoped to that feature, and stays optional to core reading and navigation.
- The shared theme persistence script uses `sessionStorage`, `matchMedia`, and `document.documentElement.dataset` to keep a manual theme choice in the current tab session.
- The `/write` page may load Tally's widget script for the embedded form. Its inline loader stays scoped to that page, uses direct browser APIs, and keeps the publish root free of standalone JavaScript assets.
- Before adding shared JavaScript, compare its main-thread and performance cost with the user problem it solves.
- The build uses `site.toml` `url` for canonical URLs and Atom feed IDs.
- The build uses the current build URL for feed self links, feed alternate links, and absolute URLs inside feed entry content.
- The Atom feed includes XHTML extension markup for a browser-facing subscription guide, shared heading links, and visible linked entry URLs.
- The browser-facing feed view is the Atom XML styled directly by `/feed.css`; it does not use XSLT.
- A work may be a single file under `works/` or under one section folder: `<slug>.md` or `<slug>.html`.
- A folder work may live directly under `works/` or under one section folder. It contains exactly one body file: `index.md`, `body.html`, or one other `*.md` file.
- A folder work publishes non-hidden files beside its work page. Markdown image references such as `![](./image.png)` resolve to those local assets.
- Markdown and HTML work files may start with TOML front matter between `+++` lines. Work metadata may define `created`, `updated`, `atom_id`, and `aliases`.
- Folder works may keep legacy `meta.toml` with the same metadata fields. A folder work uses either front matter or `meta.toml`, not both.
- Missing work `created` and `updated` values derive from Git history for the body file, with filesystem modified time as the local fallback. Missing `atom_id` derives from `site.toml` `url` and the work slug.
- Section folders match `home.md` section names by normalized folder name.

## Requirements
1. The project defines one local build command at `./build-site`.
2. That command reads one site root from `site.toml`, `home.md`, `feed.md`, and `works/`.
3. That command writes one publish root and removes stale published files from it.
4. The publish root contains public pages, work assets, `/write` when a Tally link exists, `/feed.xml`, `/feed.css`, `/site.css`, shared public assets such as self-hosted fonts, first-party inline feature scripts, and no standalone JavaScript assets. `/write` may reference Tally's widget script when it embeds a Tally form.
5. The publish root leaves out source-only files and build-only files.
6. The build validates the required source fields, unsupported source fields, duplicate published paths, and broken explicit internal links written by the author. Unmatched wikilinks do not fail the build.
7. The same site root and build URL produce the same publish root and public paths.
8. On failure, the build stops and reports the file and rule that caused the failure.
9. If the repo defines a GitHub Pages workflow, that workflow publishes the built `public/` root from the same build logic as the local command.
10. The build writes Atom 1.0 at `/feed.xml`.
11. The build links `/feed.xml` to `/feed.css` through `<?xml-stylesheet type="text/css" ...?>`.
12. The build writes line-broken, indented XML for `/feed.xml`.
13. The host serves `/feed.xml` as XML, not `application/atom+xml`. Prefer `application/xml; charset=utf-8`.
14. Local preview and browser-check commands release any ports they bind before the task finishes.

## Acceptance Checks
1. Run `./build-site <site-root> <publish-root>` against the full-output examples and inspect the publish root against the behavior named in each `expected.md`.
2. Build one unchanged example twice and compare the publish roots.
3. Run the named validation cases for build failures in `agent_docs/examples/validation-severity.md`.
4. After running a local preview or browser check, verify the ports used by that task are no longer listening.
