# Expected Outcome

- `field-notes` renders self-linking body headings with ids `materials`, `turn`, `turn-2`, and `marks`.
- `field-notes` keeps the work header to the title and places the publish date at the top of the margin-note track as muted metadata.
- Those self-linking body headings keep a plain heading treatment without an underline.
- The left rail nests linked section entries for `Materials`, `Turn`, and `Turn` under `Field Notes` as one close-set list with a guide line and current-entry dot.
- The left rail shows `Other works` as a static section label and lists `Garden Path`.
- The link to `[[Garden Path]]` resolves to the published path `/garden-path` and reads as a body link without a heavy underline.
- The external link to `https://archive.example/atlas` uses the appended link marker without a heavy underline.
- The Atom feed entry for `Field Notes` rewrites `Garden Path` and `Archive Atlas` to absolute URLs inside entry content.
- `garden-path` renders a backlinks section after the body content listing `Field Notes`.
