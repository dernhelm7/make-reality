# Labyrinth

Labyrinth is a static site generator for the personal publishing site described in [agent_docs/README.md](agent_docs/README.md).
The product aim and ownership rules live under `agent_docs/`; this README only documents the local command surface.

## Build

Run the local build command with one site root and one publish root:

```sh
./build-site [--build-url <url>] <site-root> <publish-root>
```

Example:

```sh
./build-site agent_docs/examples/minimal-markdown /tmp/labyrinth-out
```

Use `--build-url` when the current build should point at a different host than `site.toml` `url`:

```sh
./build-site --build-url http://localhost:8000 site /tmp/labyrinth-preview
```

The command also works when called by absolute path from outside the repo root.

## Preview

Run the preview helper from any directory:

```sh
/Users/dernhelm/Projects/Labyrinth/preview-site
```

That builds the starter site to `/tmp/labyrinth-preview` and serves it at `http://localhost:8000`.
The preview helper sets `http://localhost:<port>` as the build URL, so feed links and other absolute preview targets stay local.
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

The repo includes a GitHub Pages workflow at [deploy-pages.yml](/Users/dernhelm/Projects/Labyrinth/.github/workflows/deploy-pages.yml). It runs the local test suite, builds `site/` to `public/` with [build-site](/Users/dernhelm/Projects/Labyrinth/build-site), uploads that publish root, and deploys it through GitHub Pages on pushes to `main`.

Before it will publish, set the repository Pages source to `GitHub Actions` in GitHub.

The build emits relative page and asset links, so the published HTML works at a domain root or under a subpath without changing the renderer.
Set `site/site.toml` `url` to the deployed site URL for canonical URLs and Atom IDs.
Use `--build-url` only when one build needs a different output host, such as local preview or a review deploy.

Examples:

- custom domain: `https://yourdomain.com`
- user site: `https://<username>.github.io`
- project site: `https://<username>.github.io/<repo>`
