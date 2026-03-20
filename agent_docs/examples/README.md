# Examples

This folder contains canonical source fixtures, expected outcomes, and one validation reference table for the spec.

Each fixture directory is one self-contained site root. Each fixture includes:

- source input files
- one `expected.md` file that records the observable outcome the build must produce

Use these examples to keep the spec, future implementation, and future tests aligned.

Keep each example small and focused. When a rule changes, update the owning spec and the affected example in the same change.

Current entries:

- `minimal-markdown`: one Markdown work with derived defaults
- `metadata-overrides`: one work with explicit metadata overrides
- `html-work`: one authored HTML work, including author-provided JavaScript
- `section-fallback`: one work whose section falls back to `Other works`
- `wikilinks-and-assets`: wikilinks, referenced assets, and unreferenced assets
- `validation-severity.md`: named `fatal` and `recoverable` cases
