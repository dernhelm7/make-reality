# Non-Default Guesses

This file records implementation choices that were not fully pinned down by the spec.

## Current guesses

- The publish root uses `index.html` files inside `/<slug>/` and `/works/` directories so the public URLs still stay slashless while the output remains portable across static hosts.
- Works sort newest-first on `/works`, with title as the stable tie-breaker.
- The loader accepts `sections` when the key is nested under the final `contact_links` or `gift_links` table because the canonical example `site.toml` files use that TOML layout.
- The shared stylesheet uses an ET Book-first font stack, but the repo does not yet ship font files to self-host it. The fallback serif stack keeps the build usable until author-supplied font assets exist.
- `design-samples.html` is treated as visual direction, not as a literal output contract. The generator uses a smaller shared set of primitives such as `page-surface`, `page-head`, `works-entry`, and `reading-prose` to reach the same feel with less template-specific markup.
