# Validation Severity Cases

Use these named cases when defining or testing validation behavior.

| Case | Severity | Expected Behavior | Owning Doc |
| --- | --- | --- | --- |
| `missing-site-title` | `fatal` | Stop cleanly and write no new output. Report that `site.toml.title` is required. | `bones.md` |
| `invalid-created` | `fatal` | Stop cleanly and write no new output. Report that `created` must use the timestamp type. | `bones.md` |
| `both-main-source-files` | `fatal` | Stop cleanly and write no new output. Report that a work may not contain both `index.md` and `index.html`. | `bones.md` |
| `missing-referenced-asset` | `recoverable` | Finish the build, report the missing asset path clearly, and write inspectable output for the affected work page. | `build.md` |
| `missing-canonical-link` | `recoverable` | Finish the build, report the failed output validation clearly, and write inspectable output for the affected page. | `web-rules.md` |
