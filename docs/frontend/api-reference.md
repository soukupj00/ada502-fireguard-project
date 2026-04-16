# Frontend API Reference

Generated frontend API docs are published from TypeDoc output.

## Entry Points

- Main module index: [Modules](reference/README.md)
- Public hooks: [Functions](reference/functions/useLocationStream.md)
- Domain models: [Interfaces](reference/interfaces/FireRiskReading.md)
- Shared aliases: [Type Aliases](reference/type-aliases/GeoJSONResponse.md)

## What Is Included

The generated reference now includes:

- Public hooks exported from `frontend/src/index.ts`
- API/domain types from `frontend/src/lib/types.ts`
- Frontend-specific supporting types exported via index

If these pages are missing locally, run:

```bash
npm --prefix frontend run docs:api
mkdir -p docs/frontend/reference
cp -R frontend/dist/docs/reference/. docs/frontend/reference/
```
