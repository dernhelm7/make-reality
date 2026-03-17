# Bones

## 1. Purpose
This document defines the content model for the site.

## 2. Decisions Owned
- The structure of `site.toml`
- The structure of `works/<slug>/`
- The timestamp type
- Work metadata fields
- Supported source formats for works
- Supported media
- Override and fallback behavior for derived data

## 3. Requirements

### 3.1 Site-Level Config
1. The site root contains one `site.toml` file.
2. `site.toml` defines these top-level fields:
   - `url`: the canonical site base URL as an absolute URL with no trailing slash
   - `title`: the site title as a string
   - `statement`: the one-line site statement as a string
   - `contact_links`: an ordered list of links
   - `gift_links`: an ordered list of links
   - `sections`: an ordered list of works sections
3. Each entry in `contact_links` and `gift_links` contains `label` and `href`.
4. Each entry in `sections` contains:
   - `id`: the stable section key used by work metadata
   - `title`: the reader-facing section title shown on `/works`
5. `sections` may be empty. When it is empty, all works appear in `Other works`.

### 3.2 Work Folder Structure
1. Each work lives in its own folder at `works/<slug>/`.
2. The folder name is the public slug and is published at `/<slug>`.
3. A slug uses lowercase letters, numbers, and hyphens only.
4. Each work folder contains exactly one main source file:
   - `index.md` for a Markdown work
   - `index.html` for an HTML work
5. Each work folder contains `meta.toml` for metadata.
6. A work folder may also contain:
   - `work.css` for page-specific styles
   - local asset files referenced by the work
7. A work folder may not contain both `index.md` and `index.html`.

### 3.3 Timestamp Type
1. The site uses one timestamp type for stored timestamps and for machine-readable timestamps in HTML.
2. The timestamp type is a UTC RFC 3339 timestamp formatted as `YYYY-MM-DDTHH:MM:SSZ`.

### 3.4 Work Metadata
1. `meta.toml` requires `created`.
2. `created` uses the timestamp type.
3. `meta.toml` may also define:
   - `title`
   - `summary`
   - `section`
   - `index_title`
4. `summary` is a short plain-language summary used on the work page and the works index.
5. `section` matches a `sections[].id` value from `site.toml`.
6. `index_title` overrides the work label shown on `/works` only.

### 3.5 Derived Defaults
1. The resolved slug comes from the work folder name.
2. When `title` is not set, the build derives it by replacing hyphens with spaces and title-casing the words.
3. When `index_title` is not set, the works index uses the resolved `title`.

### 3.6 Source Formats And Media
1. `index.md` uses CommonMark as its base syntax.
2. Supported wikilinks in `index.md` are `[[Note]]` and `[[Note|Label]]`.
3. A wikilink target matches a published work when the target, normalized with the site's slug rules, equals the work slug.
4. When a wikilink target matches a published work, the build rewrites it to that work's canonical URL.
5. When a wikilink target does not match a published work, the build keeps the visible label text and removes the hyperlink.
6. Supported content includes text, links, images, captions, and native audio.
7. `work.css` applies to its own work page only.
8. Local asset files stay beside the work source so each work is self-contained.

### 3.7 Override Rules
1. Explicit metadata overrides derived defaults.
2. An explicit `section` value places a work in that configured section when the section exists.

## 4. Acceptance Checks
1. Confirm that `site.toml` matches the required fields.
2. Confirm that a work folder matches the required and optional files.
3. Confirm that the timestamp type is defined once and used for `created` and other machine-readable timestamps.
4. Confirm that a work with `meta.toml` containing only `created` still resolves a root-level public slug, title, and created timestamp.
5. Confirm that a work with no `created` fails validation.
6. Confirm that a derived title is made by replacing hyphens with spaces and title-casing the words.
7. Confirm that `index_title` changes the label on `/works` without changing the page title.
8. Confirm that `index.md` supports CommonMark plus wikilinks.
9. Confirm that images and native audio are part of the supported content set.

## 5. Open Questions
None.
