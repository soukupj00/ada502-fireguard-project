# Getting Started

## Local preview

1. Install docs dependencies:

```bash
uv sync --project docs
```

2. Generate frontend API docs:

```bash
npm --prefix frontend run docs:api
mkdir -p docs/frontend/reference
cp -R frontend/dist/docs/reference/. docs/frontend/reference/
```

3. Build and serve docs:

```bash
PYTHONPATH=backend/src:intelligence-system/src uv run --project docs mkdocs serve
```

## Update workflow

- Add or improve Python docstrings in backend/intelligence modules.
- Keep frontend public API exported from `frontend/src/index.ts`.
- Add architecture and operational notes in markdown pages.
- Push to `main` to publish updated docs automatically.
