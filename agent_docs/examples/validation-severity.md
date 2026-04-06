# Validation Cases

Use these named cases when defining or testing validation behavior. The main spec says the build should fail clearly; this table carries the validation cases the spec still owns.

| Case | Expected Behavior | Owning Doc |
| --- | --- | --- |
| `missing-required-field` | Report the missing field clearly. | `build.md` |
| `duplicate-published-path` | Report the conflicting published path clearly. | `build.md` |
| `missing-work-reference` | Report the missing work target clearly. | `build.md` |
| `broken-internal-link` | Report the broken internal link clearly. | `build.md` |
| `missing-canonical-link` | Report the failed output validation clearly. | `web-rules.md` |
