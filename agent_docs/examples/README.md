# Examples

This folder contains canonical source fixtures, expected outcomes, and one validation reference table for the spec.

Each fixture directory is one self-contained site root plus one `expected.md` file that records the observable outcome the build must produce.

Examples may show one accepted file layout, naming convention, or created-date shape. Treat those as concrete examples unless a main spec doc makes them a general requirement.
Each `expected.md` should record only the exact outcomes worth checking for its fixture. Do not restate generic success or common output files unless the fixture adds a distinct case.

Keep each example small and focused. When a rule changes, update the owning spec and the affected example in the same change.

Current entries:

- `minimal-markdown`: one Markdown work with derived defaults
- `named-sections`: works assigned to named sections from `home.md`, with section descriptions and one empty shelf
- `html-work`: one authored HTML body fragment, including author-provided JavaScript
- `reading-microfeatures`: automatic heading anchors, linked section index, backlinks, and link treatment
- `section-fallback`: one work whose section falls back to `Other works`
- `wikilinks-and-assets`: wikilinks, aliases, and missing-link fallback
- `validation-severity.md`: named validation cases
- `fluid-type-scale.css`: illustrative stylesheet reference — colors, fluid type scale, and cursor

Coverage groups:

- `source-model fixtures`: `minimal-markdown`, `named-sections`, `section-fallback`, `html-work`, `wikilinks-and-assets`, `reading-microfeatures`
- `page-shape fixtures`: `minimal-markdown`, `named-sections`, `section-fallback`, `reading-microfeatures`
- `full-output fixtures`: `minimal-markdown`, `html-work`, `wikilinks-and-assets`, `reading-microfeatures`
- `web-output fixtures`: `minimal-markdown`, `html-work`, `reading-microfeatures`
- `reading-layout fixture`: `reading-microfeatures`
