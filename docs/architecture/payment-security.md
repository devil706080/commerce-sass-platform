# Payment and card-data boundary

## Non-negotiable rule

The platform must never collect, receive, process, store or transmit raw PAN/card number, CVV/CVC, PIN/PIN block or magnetic-stripe track data. Card collection belongs to a payment service provider (PSP) using its hosted checkout page, hosted fields or approved tokenization flow. Select the provider and integration only after an ADR and provider-specific compliance review.

## Masking requirements

- Card entry is rendered/hosted by the PSP so card data is posted directly to the PSP, not to our API or frontend application server.
- Our UI may display limited metadata supplied by the PSP, e.g. `Visa •••• 4242`.
- Store only allowlisted provider references and safe display metadata needed for receipts/account display.
- Never store CVV/CVC, even encrypted, hashed or masked. Never log raw payment request/response bodies.
- Never place PAN/CVV, payment secrets or full provider payloads in Redis, Kafka, logs, traces, analytics or support exports.

## Payment service responsibilities

- Create PSP payment sessions/intents using server-side credentials.
- Persist only provider references, amount/currency, status, idempotency reference and approved masked display metadata.
- Verify webhook signatures and provider event IDs.
- Make webhook handling idempotent and resilient to duplicate/out-of-order delivery.
- Reconcile provider state; browser return URLs are not proof of payment.
- Support refunds through authorized backend workflows with audit events and appropriate confirmation.
- Keep per-tenant PSP credentials isolated and encrypted; do not expose them to storefront clients.

## Separate billing concerns

Customer payments for a tenant's products are distinct from the SaaS platform charging tenants subscription/usage fees. These may use different PSP accounts, ledgers and permissions. Do not mix the two flows in one table or UI without an approved architecture decision.

## Verification gates

- Inspect browser/network flow to verify PAN/CVV do not reach platform origins.
- Automated tests scan request logs, events, traces and persisted schemas for prohibited fields.
- Verify signed webhooks, replay handling, idempotency and refund authorization.
- Review PSP configuration and PCI scope with the PSP/acquirer and a qualified assessor.
