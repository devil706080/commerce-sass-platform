# Customer storefront

**Status:** Folder placeholder only. The app runtime will be scaffolded after the frontend workspace and app contracts are approved.

Public, tenant-branded shopping experience. Owns browse/search, product detail, account experience, cart UI, checkout UI and order tracking screens. Calls backend APIs only.

## Expected app structure

```text
storefront/
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
