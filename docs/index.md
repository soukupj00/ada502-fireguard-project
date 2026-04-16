# FireGuard Documentation

This site documents the FireGuard platform end-to-end:

- FastAPI backend API and internals
- Intelligence system worker and risk processing modules
- Frontend architecture and TypeScript API surface
- Deployment and contributor workflow for docs

## Auto-generated and maintained docs

The docs pipeline combines:

- Python API references from docstrings using `mkdocstrings`
- Frontend TypeScript API docs from `TypeDoc`
- Manual architecture pages for system-level understanding

All pages are rebuilt on push to `main` and published to GitHub Pages.
A parallel deployment path serves the same docs in-cluster under `/docs`.
