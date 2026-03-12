# Shape

This file defines the launch website's structure: page URLs, page purposes, sections, navigation, and launch boundary.

## Launch Pages

The launch site must define exactly three page types:

- `/` is the homepage.
- `/works/` is the works index.
- `/works/<slug>/` is a work page.

## Homepage

The homepage must function as a cover/title page.

It must contain:

- the site title
- a short introduction
- a primary link to `/works/`
- the shared navigation
- the shared footer

It must also surface the featured work as a secondary link.

## Navigation

The site must use one consistent navigation and footer pattern on every page.

The header navigation must contain:

- `Home`, linking to `/`
- `Works`, linking to `/works/`

The footer must contain:

- the contact email defined in `kinds.md`
- the support links defined in `kinds.md`

Navigation labels are fixed for launch and must use `Home` and `Works`.

## Works Index

The works index must act as the site's table of contents.

It must:

- render section headings in the order defined by `works_index`
- render work entries inside each section in the order defined by `works_index`
- show each work's title as the primary link
- show each work's summary with the title
- show the published date when `published` is present

The works index is the only launch page that groups multiple works.

## Work Page

Each work page must contain:

- the work title
- the work summary as a standfirst
- the published date when `published` is present
- the updated date when `updated` is present and differs from `published`
- the body content
- the shared navigation
- the shared footer
