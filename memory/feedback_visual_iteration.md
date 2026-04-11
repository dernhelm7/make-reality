---
name: Visual iteration feedback
description: How the user wants to approach interface work — show don't tell, screenshot-first
type: feedback
---

Always serve the output over HTTP (not file://) before asking the user to review — root-relative asset paths break when opened directly.

When iterating on layout/typography, ask for a screenshot before making changes. Don't assume what "off proportions" means — the specific problem (spacing too loose, dots sub-pixel, section label cramped) only becomes clear from seeing the actual render.

**Why:** First round of ToC work produced visually correct structure but wrong proportions; corrections required a screenshot to diagnose accurately.

**How to apply:** After any visual change, prompt the user to refresh and share a screenshot rather than describing changes and waiting for vague feedback. When spacing or typography feels "off", look at the rendered px values — `0.06rem dotted` renders as a hairline at large font sizes; `0.55rem` padding sounds small but reads as large gaps in a fluid type scale.
