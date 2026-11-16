# Open Business, Compliance and Operations Decisions

# Part F — Open Business, Compliance and Operations Decisions

# Open business, compliance and operations decisions

These items are deliberately visible. AI agents must not resolve them by guessing. They do not block local Compose startup or basic Control Plane development, but affected production features must remain disabled until the decision is recorded and reviewed.

| ID | Decision | Current safe default | Owner / evidence required | Blocks |
|---|---|---|---|---|
| BIZ-001 | Merchant of record and settlement | Each tenant is the seller and connects its own PSP merchant account; no split settlement | Business/legal + PSP/acquirer confirmation | Live payment and settlement |
| BIZ-002 | PSP vendor and methods | Provider adapter + sandbox first; India PSP vendor open | Merchant onboarding, hosted checkout and webhook documentation | Live UPI/card/COD policy |
| REG-001 | Product-category eligibility by tenant/jurisdiction | Default-deny restricted categories; no regulated category is sellable until verified | Regulatory/legal expert and tenant licence evidence | Medicines, medical devices, supplements and other restricted categories |
| TAX-001 | Tax ownership/calculation/registration | Store tax breakdown snapshots; do not invent rates | Accountant/tax advisor and tenant registrations | Real checkout/invoices |
| PRIV-001 | Privacy, retention, deletion and legal holds | Minimize PII and implement deletion workflows only under approved retention rules | Privacy/legal review per operating jurisdiction | Production customer data |
| BIZ-003 | SaaS subscription plans and billing | Separate future SaaS billing context from customer product-payment service | Platform business decision | Charging tenants for SaaS |
| OPS-001 | Tenant-count/concurrency target | Establish a load-test baseline before promising capacity | Product owner and engineering | Capacity and pool sizing |
| OPS-002 | RPO/RTO and backup cadence | No production database launch without tested recovery targets | Business/operations | Production database |
| OPS-003 | EC2 deployment topology | One EC2 + Compose may be a pilot only, not HA | Budget, uptime target, operational ownership | Public production deployment |
| OPS-004 | Production secrets/object store/logging | Use provider adapters; choose AWS services in a future EC2 ADR | Security/operations | EC2 deployment |
| COM-001 | Returns for regulated products | Fail closed until category-specific return/refund policy is approved | Regulatory/legal + PSP | Regulated-product returns |

Decision log format: record the decision, date, owner, evidence, affected ADRs, assumptions, consequences and review date under `docs/adr/` or `docs/decisions/`. Do not expose sensitive licence or merchant credentials in this register.

---
