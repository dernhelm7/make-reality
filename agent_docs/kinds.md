# Kinds

This file defines the launch content kinds, metadata, source-of-truth rules, and asset conventions.

## Source of Truth

Launch content must come from these sources:

- `content/site.toml` for site-level content
- `content/works-index.toml` for works-index section titles and work order
- `content/works/<slug>.md` for each work

## Site Content

`content/site.toml` must define:

- `site_title`: required string
- `intro`: required short paragraph
- `contact_email`: required email address
- `support_links`: required ordered list of support links

Each `support_links` entry must define:

- `label`: required string
- `url`: required absolute URL

The order of `support_links` is the order rendered in the footer.

## Works Index Data

`content/works-index.toml` must define an ordered `sections` list.

Each section must define:

- `title`: required string
- `entries`: required ordered list of work slugs

Each slug in `entries` must match exactly one work file in `content/works/`.

Section order and entry order are the source of truth for `/works/`.

## Work

Each work file in `content/works/<slug>.md` must define:

- `slug`: required string and URL segment
- `title`: required string
- `summary`: required short summary
- `published`: optional ISO date
- `updated`: optional ISO date
- `featured`: required boolean

The Markdown body of the file is the work body.

For launch:

- exactly one work must set `featured = true`
- the launch work must be an evergreen written piece

## Assets

If a work uses local assets, they must live under `public/works/<slug>/`.

Asset paths must remain stable when the site is built into `/dist/`.
