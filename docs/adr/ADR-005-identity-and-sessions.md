# ADR-005: Identity and session strategy

- Status: Proposed — human review required
- Decision direction: Separate platform operator identities from tenant customer and staff identities. Use OIDC Authorization Code + PKCE S256 for external identity providers; Argon2id for local passwords; secure server-managed sessions/refresh rotation; MFA for privileged roles.
- Open: Decide account linking, global-vs-tenant customer identity semantics, session revocation and provider selection before Identity implementation.
