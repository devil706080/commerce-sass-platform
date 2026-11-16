# Platform administration console

**Status:** Folder placeholder only. The app runtime will be scaffolded after the frontend workspace and app contracts are approved.

SaaS operator application for tenant onboarding, verification, provisioning status, plans/entitlements, platform support operations and audit views. Never exposes tenant commerce data by default.

## Expected app structure

```text
platform-console/
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
