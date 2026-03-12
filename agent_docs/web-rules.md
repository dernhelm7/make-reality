# Web Rules

This file defines the website's shared web requirements: semantic HTML, accessibility, reduced motion, responsive behavior, performance, and validation.

## Semantic HTML

Every page must contain:

- a skip link before the main navigation
- a `header`
- a `main`
- a `footer`

Every page must use exactly one `h1`.

The shared navigation must use a `nav` element.

The works index must use:

- `h2` for section headings
- an ordered list for section entries
- one list item per work entry
- a `time` element for dates when dates are shown

## Accessibility

The site must meet these minimum accessibility rules:

- keyboard navigation must reach all interactive elements
- focus states must remain clearly visible
- text and essential UI must meet WCAG AA contrast targets
- link text must describe the destination
- heading levels must stay sequential

The contact email must be a usable link.

## Responsive Behavior

The layout must remain usable from 320px wide screens upward.

On narrow screens:

- content must stay in a single column
- navigation must remain readable without horizontal scrolling

On wide screens:

- work pages must preserve a narrow reading measure
- large empty margins should support reading rather than create dead space

## Motion

Motion must remain restrained.

Allowed motion is limited to brief CSS transitions on color, opacity, or border treatment.

When `prefers-reduced-motion: reduce` is present, decorative transitions must be removed.

## Performance

Generated output must be static HTML and CSS only.

The launch site should ship:

- one primary CSS file
- no JavaScript in generated output
- optimized local assets when assets are present

## Validation

The implementation must validate:

- required content fields
- duplicate or missing slugs
- works-index entries that reference missing works
- broken internal links
- valid HTML output
