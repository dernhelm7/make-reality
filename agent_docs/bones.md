# Bones

## 1. Purpose
This document defines the source model for the site and the resolved site and work models the build uses everywhere else.

## 2. Decisions Owned
- The required source inputs
- The structure of `site.toml`
- The resolved site model
- The structure of `works/<slug>/`
- The stored and visible date forms
- Work metadata fields
- Derived defaults
- Supported source formats, local assets, and wikilinks

## 3. Requirements

### 3.1 Source Root
1. The site root contains one `site.toml` file and one `works/` directory.
2. The build treats every direct child folder of `works/` as one candidate work.

### 3.2 Site Config
1. `site.toml` requires these top-level fields:
   - `url`: the canonical site base URL as an absolute URL with no trailing slash
   - `lang`: the document language as a BCP 47 language tag
   - `title`: the site title as a string
   - `statement`: the one-line site statement as a string
   - `contact_links`: an ordered list of links
   - `gift_links`: an ordered list of links
   - `sections`: a list of works sections
2. Each entry in `contact_links` and `gift_links` contains `label` and `href`.
3. Each entry in `sections` contains:
   - `number`: unique section number used by work metadata and section order
   - `title`: the reader-facing section title shown on `/works`
4. `contact_links` and `gift_links` each contain at least one link. `sections` may be empty.

### 3.3 Resolved Site Model
1. The build resolves `site.toml` into one site record with these fields: canonical URL, document language, title, statement, ordered contact links, ordered gift links, and sections ordered by ascending section number.
2. The resolved site record is the source of truth for the homepage content, the global links block, the works index section order, the feed channel metadata, and site-wide document metadata.

### 3.4 Work Folder Structure
1. Each work lives in `works/<slug>/`. The folder name is the public slug; the work is published at `/<slug>`.
2. A slug uses lowercase letters, numbers, and hyphens only and must not use a reserved top-level path. Reserved: `works`.
3. Each work folder contains exactly one main source file (`index.md` for Markdown, `index.html` for HTML), `meta.toml`, optionally `work.css`, and optionally local asset files named by the work body. It may not contain both `index.md` and `index.html`.

### 3.5 Stored And Visible Dates
1. The timestamp type is a UTC RFC 3339 timestamp formatted as `YYYY-MM-DDTHH:MM:SSZ`, used for stored timestamps and machine-readable timestamps in HTML.
2. Visible dates are derived from the stored timestamp and rendered in UTC as a full month name, day number, and four-digit year, for example `February 14, 2020`.

### 3.6 Work Metadata
1. `meta.toml` requires `created`.
2. `created` uses the timestamp type.
3. `meta.toml` may also define:
   - `title`: derived from the slug when it is absent
   - `summary`: a short plain-language summary shown on the work page and the works index
   - `section`: names the preferred section for the work by section number
   - `index_title`: overrides the work label shown on `/works` only

### 3.7 Resolved Work Model
1. The resolved slug comes from the work folder name.
2. The resolved canonical URL joins the resolved site canonical URL with `/<slug>`.
3. When `title` is not set, the build derives it by replacing hyphens with spaces and title-casing the words.
4. When `index_title` is not set, the works index uses the resolved `title`.
5. When `section` names a configured section number, section placement uses that section.
6. When `section` is missing, names no configured section, or `sections` is empty, section placement uses the final fallback section named `Other works`.
7. Each valid work resolves to one record with these reader-facing fields: slug, canonical URL, title, index label, created timestamp, visible date, summary, and section placement. This record is the source of truth for work pages, works index entries, feed items, and wikilink resolution.

### 3.8 Source Formats And Local Media
1. `index.md` uses CommonMark as its base syntax.
2. Supported wikilinks in `index.md` are `[[Note]]` and `[[Note|Label]]`.
3. To normalize a wikilink target, the build lowercases it, replaces spaces and underscores with hyphens, removes characters other than lowercase letters, numbers, and hyphens, collapses repeated hyphens, and trims leading and trailing hyphens. A target matches a published work when its normalized form equals the work slug.
4. These normalization examples define the expected result:

   | Input | Normalized |
   | --- | --- |
   | `Folded Map` | `folded-map` |
   | `__note__` | `note` |
   | `café` | `caf` |

5. When a wikilink target matches a published work, the build rewrites it to that work's canonical URL. When it does not match, the build keeps the visible label text and removes the hyperlink.
6. Authored `index.html` provides body content for that work page. It may not use `h1`. It may include author-provided JavaScript.
7. `work.css` may define work-specific CSS for that work page.
8. Local asset files stay beside the work source so each work is self-contained.
9. The work body names each local asset file it uses.
10. A local asset file is publishable when the work body references it and the file is in the same work folder.

## 4. Acceptance Checks
1. Build `agent_docs/examples/minimal-markdown` and confirm that `site.toml` resolves to one site record and that the work resolves to the values listed in `expected.md`, including derived defaults.
2. Build `agent_docs/examples/metadata-overrides` and `agent_docs/examples/section-fallback` and confirm that explicit metadata and fallback section placement resolve to the values listed in each `expected.md`.
3. Build `agent_docs/examples/wikilinks-and-assets` and confirm that wikilinks and publishable local assets resolve according to `expected.md`.

## 5. Open Questions
None.
