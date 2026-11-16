# ADR-006: Payment boundary

- Status: Proposed — human review required
- Decision direction: PSP-hosted checkout/hosted fields/tokenization. No PAN/CVV enters platform systems. Store PSP references and approved card display metadata only. Payment service owns PSP integration, webhook verification, refunds and reconciliation.
- Open: Merchant-of-record, tenant PSP onboarding, provider choice, settlement, refund policy and applicable PCI scope require business/qualified compliance review before live payments.
