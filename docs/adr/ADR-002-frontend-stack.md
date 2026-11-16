# ADR-002: Frontend stack

- Status: Proposed — human review required
- Decision: Three Next.js App Router + React + TypeScript applications under `frontend/apps/`; pnpm workspaces + Turborepo for frontend orchestration.
- UI: Tailwind CSS, accessible Radix/shadcn primitives and a shared neutral design-token/UI package.
- Testing: Vitest, Testing Library and Playwright; Storybook for shared UI review.
- Consequences: Separate deployable apps; do not put backend business logic in frontend packages.
