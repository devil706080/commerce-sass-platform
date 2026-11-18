# Customer storefront

Tenant-branded public shopping experience. Tenant identity is resolved from the
Control Plane's verified domain mapping and published products come from the Catalogue public API.
Browser clients never select a tenant ID and never connect to a database.

## Local runtime

- Storefront: `http://lifemac.localhost:3002`
- Public catalogue API (server-side): `http://catalogue:8010`
- Sign-in: Keycloak Authorization Code + PKCE using the `storefront` client

The storefront reads public categories from the Catalogue API. A category is
customer-visible only when at least one published product is assigned to it;
empty and draft-only categories are intentionally hidden. The current catalogue
contract supplies published product identity, content and base price. Public
image, availability and promotion contracts remain backend follow-up work; the
storefront does not fabricate those values.

## Environment

| Variable | Purpose |
| --- | --- |
| `CATALOGUE_API_INTERNAL_URL` | Server-only Catalogue service base URL |
| `CONTROL_PLANE_INTERNAL_URL` | Server-only Control Plane URL for verified tenant-domain resolution |
| `NEXT_PUBLIC_KEYCLOAK_URL` | Browser-visible Keycloak origin |
| `NEXT_PUBLIC_KEYCLOAK_REALM` | Customer identity realm |
| `NEXT_PUBLIC_KEYCLOAK_CLIENT_ID` | OIDC public client ID |

## Commands

```powershell
pnpm --filter @commerce-saas/storefront typecheck
pnpm --filter @commerce-saas/storefront build
```
