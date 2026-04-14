# Labyrinth

Labyrinth is a static site generator for the personal publishing site described in [agent_docs/README.md](agent_docs/README.md).
The product aim and ownership rules live under `agent_docs/`; this README only documents the local command surface.

## Build

Run the local build command with one site root and one publish root:

```sh
./build-site <site-root> <publish-root>
```

Example:

```sh
./build-site agent_docs/examples/minimal-markdown /tmp/labyrinth-out
```

The command also works when called by absolute path from outside the repo root.

## Preview

Run the preview helper from any directory:

```sh
/Users/dernhelm/Projects/Labyrinth/preview-site
```

That builds the starter site to `/tmp/labyrinth-preview` and serves it at `http://localhost:8000`.
The starter site includes editable sample works under `site/works/` so the default preview shows a real home page and multiple work pages.

The authoring model is intentionally small:

- Use `index.md` for headings, paragraphs, standard links, and wikilinks like `[[Work Title]]` or `[[Work Title|Label]]`.
- Use `body.html` when you need authored HTML structure such as `.sidenote`, `.marginnote`, or other custom layout inside a work body.

You can also pass a site root, publish root, and port:

```sh
/Users/dernhelm/Projects/Labyrinth/preview-site agent_docs/examples/reading-microfeatures /tmp/labyrinth-visual-check 8001
```

## Validation

Run the local checks with:

```sh
python3 -m unittest
```

The canonical fixtures and expected outcomes live in `agent_docs/examples/`.

## Deploy

The repo includes a GitHub Pages workflow at [deploy-pages.yml](/Users/dernhelm/Projects/Labyrinth/.github/workflows/deploy-pages.yml). It runs the local test suite, builds `site/` to `public/`, uploads that publish root, and deploys it through GitHub Pages on pushes to `main`.

Before it will publish, set the repository Pages source to `GitHub Actions` in GitHub.

This generator emits root-relative public URLs such as `/site.css` and `/feed.xml`, so use GitHub Pages with a root path:

- a custom domain such as `yourdomain.com`
- a user site such as `<username>.github.io`

Do not use a project-site subpath such as `<username>.github.io/Labyrinth` unless the generator gains base-path support.
