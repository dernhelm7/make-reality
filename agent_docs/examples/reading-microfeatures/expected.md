# Expected Outcome

- `field-notes` renders self-linking body headings with ids `materials`, `turn`, `turn-2`, and `marks`.
- `field-notes` renders a linked section index for the work body.
- That section index lists `Materials`, `Turn`, and `Turn` in source order and links to `#materials`, `#turn`, and `#turn-2`.
- On wide screens, the section index sits to the left of the main body column. On narrow screens, it appears before the body content.
- The link to `[[Garden Path]]` resolves to the published path `/garden-path`.
- The external link to `https://archive.example/atlas` remains external and is visibly distinguished from the internal work link without relying on color alone.
- `garden-path` renders a backlinks section after the body content listing `Field Notes`.
