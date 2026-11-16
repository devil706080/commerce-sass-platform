# Tenant administration console

**Status:** Folder placeholder only. The app runtime will be scaffolded after the frontend workspace and app contracts are approved.

Tenant staff application for catalogue, pricing, inventory, orders, promotions, content, reporting, team and settings. Enforce role/permission-aware navigation and API authorization.

## Expected app structure

```text
tenant-admin/
├── public/
├── src/
│   ├── app/
│   ├── features/
│   ├── components/
│   ├── lib/
│   └── styles/
└── tests/
```

Use shared neutral primitives from `frontend/packages/ui` and validated tokens from `frontend/packages/design-tokens`. Do not hardcode client brand names or themes. Include responsive, accessible loading, empty, error, permission-denied and success states.
