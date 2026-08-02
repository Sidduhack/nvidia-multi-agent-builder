# Frontend

React + TypeScript + Vite workspace for the multi-agent dashboard.

## Development

```bash
npm install
npm run dev
```

Vite proxies `/api/*` to the local FastAPI server at `127.0.0.1:8000` during development, keeping frontend code on relative versioned API paths.

## Boundaries

- No provider/API secrets belong in this package.
- `src/api/contracts.ts` mirrors approved Phase 5 public contracts; backend endpoints must not be invented in components.
- The Phase 7 Build Project button is deliberately disabled until endpoint implementation is wired and tested.
- Tests/build/preview states must remain truthful; absence of data is not success.

## Future structure

As implementation grows, add feature-oriented modules under `src/features/`, reusable primitives under `src/components/`, API transport under `src/api/`, and application state under `src/state/`. Avoid a single giant component.
