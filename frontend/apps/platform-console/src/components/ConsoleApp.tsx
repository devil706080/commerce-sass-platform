"use client";

import Keycloak from "keycloak-js";
import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";

type TenantStatus = "PENDING" | "PROVISIONING" | "ACTIVE" | "FAILED" | "DELETION_REQUESTED";
type Tenant = {
  id: string;
  display_name: string;
  initial_owner_email: string | null;
  status: TenantStatus;
  created_at: string;
  updated_at: string;
};
type Notice = { tone: "success" | "error" | "info"; message: string } | null;
type ProvisioningJob = { id: string; tenant_id: string; service_key: string; status: "PENDING" | "RUNNING" | "INFRASTRUCTURE_READY" | "FAILED"; attempt_count: number; error_code: string | null; };
type ServiceDatabase = { service_key: string; database_name: string; schema_name: string | null; status: string; };
type ThemeOption = { key: string; name: string; primary: string; primary_dark: string; accent: string; surface: string };
type TenantDomain = {
  id: string;
  tenant_id: string;
  hostname: string;
  purpose: "STOREFRONT" | "TENANT_ADMIN";
  verification_status: "PENDING_VERIFICATION" | "VERIFIED";
  verification_method: "LOCAL";
  verified_at: string | null;
  created_at: string;
  updated_at: string;
};

const servicePresentation: Record<string, { name: string; description: string }> = {
  identity_access: { name: "Identity & Access", description: "Tenant owner and staff memberships" },
  catalogue_fixture: { name: "Catalogue", description: "Products and categories" },
  inventory_fixture: { name: "Inventory", description: "Stock and availability" },
  media_fixture: { name: "Media", description: "Secure product image storage" },
};

const keycloak = new Keycloak({
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL!,
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM!,
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID!,
});
const api = process.env.NEXT_PUBLIC_CONTROL_API_URL!;

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    tenants: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    domain: <><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    refresh: <><path d="M20 6v5h-5M4 18v-5h5"/><path d="M18.5 9A7 7 0 0 0 6 6.5L4 9M5.5 15A7 7 0 0 0 18 17.5l2-2.5"/></>,
    trash: <><path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6"/></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3M21 19V5a2 2 0 0 0-2-2h-6"/></>,
    shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/><path d="m9 12 2 2 4-4"/></>,
    copy: <><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/></>,
    close: <><path d="m6 6 12 12M18 6 6 18"/></>,
    arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
  };
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

function StatusPill({ status }: { status: TenantStatus }) {
  const presentation: Record<TenantStatus, { className: string; label: string }> = {
    PENDING: { className: "pending", label: "Pending setup" },
    PROVISIONING: { className: "provisioning", label: "Provisioning" },
    ACTIVE: { className: "active", label: "Active" },
    FAILED: { className: "failed", label: "Setup failed" },
    DELETION_REQUESTED: { className: "deleting", label: "Deletion requested" },
  };
  const current = presentation[status];
  return <span className={`status-pill ${current.className}`}>
    <span className="status-dot" />{current.label}
  </span>;
}

export default function ConsoleApp() {
  const initialized = useRef(false);
  const [authReady, setAuthReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [name, setName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [brandName, setBrandName] = useState("");
  const [initials, setInitials] = useState("");
  const [themeKey, setThemeKey] = useState("ocean_teal");
  const [themes, setThemes] = useState<ThemeOption[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"ALL" | TenantStatus>("ALL");
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Tenant | null>(null);
  const [provisionTarget, setProvisionTarget] = useState<Tenant | null>(null);
  const [brandingTarget, setBrandingTarget] = useState<Tenant | null>(null);
  const [brandingSaving, setBrandingSaving] = useState(false);
  const [contactTarget, setContactTarget] = useState<Tenant | null>(null);
  const [contactEmail, setContactEmail] = useState("");
  const [contactSaving, setContactSaving] = useState(false);
  const [provisionServices, setProvisionServices] = useState<string[]>(["identity_access", "catalogue_fixture", "inventory_fixture", "media_fixture"]);
  const [provisioning, setProvisioning] = useState(false);
  const [confirmName, setConfirmName] = useState("");
  const [notice, setNotice] = useState<Notice>(null);
  const [view, setView] = useState<"tenants" | "provisioning" | "domains">("tenants");
  const [jobs, setJobs] = useState<ProvisioningJob[]>([]);
  const [serviceDatabases, setServiceDatabases] = useState<ServiceDatabase[]>([]);
  const [selectedProvisionTenant, setSelectedProvisionTenant] = useState<string | null>(null);
  const [selectedDomainTenant, setSelectedDomainTenant] = useState<string | null>(null);
  const [domains, setDomains] = useState<TenantDomain[]>([]);
  const [domainHostname, setDomainHostname] = useState("");
  const [domainPurpose, setDomainPurpose] = useState<"STOREFRONT" | "TENANT_ADMIN">("STOREFRONT");
  const [domainLoading, setDomainLoading] = useState(false);
  const [domainSaving, setDomainSaving] = useState(false);

  const operatorName = String(keycloak.tokenParsed?.preferred_username ?? keycloak.tokenParsed?.email ?? "Platform operator");

  async function request(path: string, init?: RequestInit) {
    try {
      await keycloak.updateToken(30);
    } catch {
      keycloak.clearToken();
      setAuthenticated(false);
      throw new Error("Your session expired. Sign in again to continue.");
    }
    const headers = new Headers(init?.headers);
    headers.set("Authorization", `Bearer ${keycloak.token}`);
    if (init?.body) headers.set("Content-Type", "application/json");
    const response = await fetch(`${api}${path}`, { ...init, headers });
    if (response.status === 401) {
      keycloak.clearToken();
      setAuthenticated(false);
      throw new Error("Your session expired. Sign in again to continue.");
    }
    return response;
  }

  async function loadTenants(showConfirmation = false) {
    setLoading(true);
    try {
      const response = await request("/api/v1/tenants");
      if (!response.ok) throw new Error(`Tenant request failed (${response.status})`);
      setTenants(await response.json());
      if (showConfirmation) setNotice({ tone: "info", message: "Tenant registry refreshed" });
    } catch {
      setNotice({ tone: "error", message: "Unable to load the tenant registry" });
    } finally {
      setLoading(false);
    }
  }

  async function loadThemes() {
    const response = await request("/api/v1/themes");
    if (!response.ok) throw new Error("Unable to load tenant themes");
    setThemes(await response.json());
  }

  async function loadProvisioning(tenantId?: string) {
    const target = tenantId ?? selectedProvisionTenant ?? tenants[0]?.id;
    if (!target) return;
    setSelectedProvisionTenant(target);
    try {
      const [jobsResponse, databasesResponse] = await Promise.all([
        request(`/api/v1/tenants/${target}/provisioning-jobs`),
        request(`/api/v1/tenants/${target}/service-databases`),
      ]);
      if (!jobsResponse.ok || !databasesResponse.ok) throw new Error("Unable to load provisioning state");
      setJobs(await jobsResponse.json());
      setServiceDatabases(await databasesResponse.json());
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to load provisioning state" });
    }
  }

  async function loadDomains(tenantId?: string) {
    const target = tenantId ?? selectedDomainTenant ?? tenants[0]?.id;
    if (!target) {
      setDomains([]);
      return;
    }
    setSelectedDomainTenant(target);
    setDomainLoading(true);
    try {
      const response = await request(`/api/v1/tenants/${target}/domains`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to load tenant domains");
      setDomains(body);
    } catch (error) {
      setDomains([]);
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to load tenant domains" });
    } finally {
      setDomainLoading(false);
    }
  }

  function openDomains(tenant: Tenant) {
    setView("domains");
    setDomainHostname("");
    setDomainPurpose("STOREFRONT");
    void loadDomains(tenant.id);
  }

  async function registerDomain(event: FormEvent) {
    event.preventDefault();
    if (!selectedDomainTenant) return;
    setDomainSaving(true);
    try {
      const response = await request(`/api/v1/tenants/${selectedDomainTenant}/domains`, {
        method: "POST",
        body: JSON.stringify({ hostname: domainHostname, purpose: domainPurpose }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to register hostname");
      setDomainHostname("");
      setNotice({ tone: "success", message: `${body.hostname} was registered for ${domainPurpose === "STOREFRONT" ? "the storefront" : "Tenant Admin"}` });
      await loadDomains(selectedDomainTenant);
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to register hostname" });
    } finally {
      setDomainSaving(false);
    }
  }

  async function verifyDomain(domain: TenantDomain) {
    setDomainSaving(true);
    try {
      const response = await request(`/api/v1/tenants/${domain.tenant_id}/domains/${domain.id}/verify`, { method: "POST" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to verify hostname");
      setNotice({ tone: "success", message: `${body.hostname} is verified for local routing` });
      await loadDomains(domain.tenant_id);
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to verify hostname" });
    } finally {
      setDomainSaving(false);
    }
  }

  async function retryJob(job: ProvisioningJob) {
    try {
      const response = await request(`/api/v1/tenants/${job.tenant_id}/provisioning-jobs/${job.id}/retry`, { method: "POST" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to retry provisioning");
      setNotice({ tone: "success", message: "Provisioning retry queued" });
      await loadProvisioning(job.tenant_id);
    } catch (error) { setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to retry provisioning" }); }
  }

  async function activateTenant() {
    if (!selectedProvisionTenant) return;
    try {
      const response = await request(`/api/v1/tenants/${selectedProvisionTenant}/activate`, { method: "POST" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Tenant is not ready for activation");
      setNotice({ tone: "success", message: "Tenant activated" });
      await loadTenants();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Tenant is not ready for activation" });
    }
  }

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    keycloak.init({ onLoad: "check-sso", pkceMethod: "S256", checkLoginIframe: false })
      .then(async (ok) => {
        setAuthenticated(ok);
        setAuthReady(true);
        if (ok) await Promise.all([loadTenants(), loadThemes()]);
      })
      .catch(() => {
        setAuthReady(true);
        setNotice({ tone: "error", message: "Authentication service is unavailable" });
      });
  }, []);

  const counts = useMemo(() => ({
    total: tenants.length,
    pending: tenants.filter((tenant) => tenant.status === "PENDING").length,
    deletion: tenants.filter((tenant) => tenant.status === "DELETION_REQUESTED").length,
  }), [tenants]);

  const visibleTenants = useMemo(() => tenants.filter((tenant) => {
    const matchesFilter = filter === "ALL" || tenant.status === filter;
    const query = search.trim().toLocaleLowerCase();
    return matchesFilter && (!query || tenant.display_name.toLocaleLowerCase().includes(query) || tenant.id.includes(query));
  }), [filter, search, tenants]);

  async function createTenant(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    try {
      const response = await request("/api/v1/tenants", {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ display_name: name, initial_owner_email: ownerEmail, storefront_display_name: brandName || name, fallback_initials: initials || null, theme_key: themeKey }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to create tenant");
      setName("");
      setOwnerEmail(""); setBrandName(""); setInitials(""); setThemeKey("ocean_teal");
      setCreateOpen(false);
      setNotice({ tone: "success", message: `${body.display_name} was added to the registry` });
      await loadTenants();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to create tenant" });
    } finally {
      setCreating(false);
    }
  }

  async function openBranding(tenant: Tenant) {
    try {
      const response = await request(`/api/v1/tenants/${tenant.id}/branding`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to load branding");
      setBrandName(body.display_name); setInitials(body.fallback_initials); setThemeKey(body.theme_key); setBrandingTarget(tenant);
    } catch (error) { setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to load branding" }); }
  }

  async function saveBranding(event: FormEvent) {
    event.preventDefault(); if (!brandingTarget) return; setBrandingSaving(true);
    try {
      const response = await request(`/api/v1/tenants/${brandingTarget.id}/branding`, { method: "PUT", body: JSON.stringify({ display_name: brandName, fallback_initials: initials || null, theme_key: themeKey }) });
      const body = await response.json(); if (!response.ok) throw new Error(body.detail ?? "Unable to update branding");
      setBrandingTarget(null); setNotice({ tone: "success", message: `${body.display_name} branding was updated` });
    } catch (error) { setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to update branding" }); }
    finally { setBrandingSaving(false); }
  }

  function openOwnerContact(tenant: Tenant) {
    setContactTarget(tenant);
    setContactEmail(tenant.initial_owner_email ?? "");
  }

  async function saveOwnerContact(event: FormEvent) {
    event.preventDefault();
    if (!contactTarget) return;
    setContactSaving(true);
    try {
      const response = await request(`/api/v1/tenants/${contactTarget.id}/owner-contact`, {
        method: "PUT",
        body: JSON.stringify({ initial_owner_email: contactEmail }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to update owner contact");
      setContactTarget(null);
      setNotice({ tone: "success", message: `Initial administrator updated for ${body.display_name}` });
      await loadTenants();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to update owner contact" });
    } finally {
      setContactSaving(false);
    }
  }

  async function requestDeletion() {
    if (!deleteTarget || confirmName.trim() !== deleteTarget.display_name) return;
    setDeleting(true);
    try {
      const response = await request(`/api/v1/tenants/${deleteTarget.id}`, { method: "DELETE" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to request deletion");
      setNotice({ tone: "success", message: `Deletion requested for ${deleteTarget.display_name}` });
      setDeleteTarget(null);
      setConfirmName("");
      await loadTenants();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to request deletion" });
    } finally {
      setDeleting(false);
    }
  }

  function openDelete(tenant: Tenant) {
    setConfirmName("");
    setDeleteTarget(tenant);
  }

  async function startProvisioning() {
    if (!provisionTarget || provisionServices.length === 0) return;
    setProvisioning(true);
    try {
      for (const service_key of provisionServices) {
        const response = await request(`/api/v1/tenants/${provisionTarget.id}/provisioning-jobs`, {
          method: "POST", body: JSON.stringify({ service_key }),
        });
        const body = await response.json();
        if (!response.ok) throw new Error(body.detail ?? "Unable to start provisioning");
      }
      setProvisionTarget(null);
      setNotice({ tone: "success", message: `Provisioning started for ${provisionTarget.display_name}` });
      await loadTenants();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to start provisioning" });
    } finally { setProvisioning(false); }
  }

  if (!authReady) return <main className="auth-page"><div className="auth-loader"><span /><p>Securing your workspace...</p></div></main>;

  if (!authenticated) return <main className="auth-page">
    <section className="auth-story">
      <div className="brand-lockup"><span className="brand-mark">C</span><span>Commerce Cloud</span></div>
      <div className="story-copy">
        <span className="kicker">Platform operations</span>
        <h1>Run every tenant from one trusted workspace.</h1>
        <p>Onboard businesses, monitor readiness and keep sensitive platform actions protected behind verified operator access.</p>
      </div>
      <div className="story-proof"><Icon name="shield" size={20}/><span>Identity secured by Keycloak and PKCE</span></div>
    </section>
    <section className="auth-panel">
      <div className="login-box">
        <span className="login-icon"><Icon name="shield" size={24}/></span>
        <p className="overline">Operator console</p>
        <h2>Welcome back</h2>
        <p>Continue through the protected identity service to access platform operations.</p>
        {notice?.tone === "error" && <div className="inline-error">{notice.message}</div>}
        <button className="primary-button wide" onClick={() => keycloak.login({ redirectUri: window.location.origin })}>
          Sign in securely <Icon name="arrow" />
        </button>
        <small>Only authorized platform operators can continue.</small>
      </div>
    </section>
  </main>;

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand-lockup"><span className="brand-mark">C</span><span>Commerce Cloud</span></div>
      <nav aria-label="Platform navigation">
        <p className="nav-label">Workspace</p>
        <button className={`nav-item ${view === "tenants" ? "active" : ""}`} onClick={() => setView("tenants")}><Icon name="tenants"/><span>Tenants</span></button>
        <button className={`nav-item ${view === "provisioning" ? "active" : ""}`} onClick={() => { setView("provisioning"); void loadProvisioning(); }}><Icon name="grid"/><span>Provisioning</span></button>
        <button className={`nav-item ${view === "domains" ? "active" : ""}`} onClick={() => { setView("domains"); void loadDomains(); }}><Icon name="domain"/><span>Domains</span></button>
      </nav>
      <div className="sidebar-user">
        <span className="user-avatar">{operatorName.slice(0, 1).toUpperCase()}</span>
        <div><strong>{operatorName}</strong><span>Platform operator</span></div>
        <button aria-label="Sign out" title="Sign out" onClick={() => keycloak.logout({ redirectUri: window.location.origin })}><Icon name="logout"/></button>
      </div>
    </aside>

    <main className="content">
      {view === "tenants" ? <header className="page-header">
        <div><p className="overline">Control plane</p><h1>Tenant registry</h1><p>Manage businesses and track their onboarding lifecycle.</p></div>
        <button className="primary-button" onClick={() => setCreateOpen(true)}><Icon name="plus"/>New tenant</button>
      </header> : view === "provisioning" ? <header className="page-header"><div><p className="overline">Control plane</p><h1>Provisioning</h1><p>Track tenant database, schema, migration and smoke-check readiness.</p></div><button className="secondary-button" onClick={() => void loadProvisioning(selectedProvisionTenant ?? undefined)}><Icon name="refresh"/>Refresh</button></header> : <header className="page-header"><div><p className="overline">Tenant routing</p><h1>Local domains</h1><p>Register and verify the hostname that resolves each tenant on this development machine.</p></div><button className="secondary-button" onClick={() => void loadDomains(selectedDomainTenant ?? undefined)} disabled={domainLoading}><Icon name="refresh"/>Refresh</button></header>}

      {notice && <div className={`notice ${notice.tone}`} role="status"><span>{notice.message}</span><button aria-label="Dismiss notification" onClick={() => setNotice(null)}><Icon name="close" size={16}/></button></div>}

      {view === "tenants" && <section className="metrics" aria-label="Tenant overview">
        <article><span className="metric-icon blue"><Icon name="tenants"/></span><div><p>Total tenants</p><strong>{counts.total}</strong><small>Registered businesses</small></div></article>
        <article><span className="metric-icon amber"><span className="pulse-dot"/></span><div><p>Pending setup</p><strong>{counts.pending}</strong><small>Awaiting provisioning</small></div></article>
        <article><span className="metric-icon coral"><Icon name="trash"/></span><div><p>Deletion requests</p><strong>{counts.deletion}</strong><small>Awaiting offboarding review</small></div></article>
      </section>}

      {view === "provisioning" && <section className="registry-card provisioning-dashboard">
        <div className="registry-toolbar"><label className="tenant-selector">Tenant<select value={selectedProvisionTenant ?? ""} onChange={(event) => void loadProvisioning(event.target.value)}><option value="" disabled>Select tenant</option>{tenants.map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.display_name}</option>)}</select></label></div>
        <div className="provisioning-summary"><strong>{tenants.find((tenant) => tenant.id === selectedProvisionTenant)?.display_name ?? "Select a tenant"}</strong><span>{serviceDatabases.length} schema records</span>{selectedProvisionTenant && tenants.find((tenant) => tenant.id === selectedProvisionTenant)?.status === "PROVISIONING" && <button className="primary-button compact" title={jobs.every((job) => job.status === "INFRASTRUCTURE_READY") ? "Check activation readiness" : "Wait for every provisioning job to complete"} disabled={!jobs.length || !jobs.every((job) => job.status === "INFRASTRUCTURE_READY")} onClick={() => void activateTenant()}>Activate when ready</button>}</div>
        <div className="job-list">{jobs.map((job) => <article className="job-card" key={job.id}><div><strong>{servicePresentation[job.service_key]?.name ?? job.service_key}</strong><small>Attempt {job.attempt_count}</small></div><StatusPill status={job.status === "INFRASTRUCTURE_READY" ? "PROVISIONING" : job.status === "FAILED" ? "FAILED" : "PROVISIONING"}/><span className="job-state">{job.status === "INFRASTRUCTURE_READY" ? serviceDatabases.find((item) => item.service_key === job.service_key)?.schema_name ?? "Schema ready" : job.error_code ?? job.status}</span>{job.status === "FAILED" && <button className="secondary-button compact" onClick={() => void retryJob(job)}>Retry</button>}</article>)}{jobs.length === 0 && <div className="empty-state"><h3>No provisioning jobs</h3><p>Select a tenant and start provisioning from the Tenants view.</p></div>}</div>
      </section>}

      {view === "domains" && <section className="registry-card domain-dashboard">
        <div className="registry-toolbar domain-toolbar">
          <label className="tenant-selector">Tenant<select value={selectedDomainTenant ?? ""} onChange={(event) => { setDomainHostname(""); void loadDomains(event.target.value); }}><option value="" disabled>Select tenant</option>{tenants.map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.display_name}</option>)}</select></label>
          <span className="environment-badge">Local adapter</span>
        </div>
        {selectedDomainTenant ? <>
          <div className="domain-intro"><div><strong>{tenants.find((tenant) => tenant.id === selectedDomainTenant)?.display_name}</strong><p>Register one hostname for the customer storefront and one for the tenant administration portal. Local <code>*.localhost</code> hostnames verify without editing environment configuration.</p></div><span>{domains.filter((domain) => domain.verification_status === "VERIFIED").length} verified</span></div>
          <form className="domain-form" onSubmit={registerDomain}><label htmlFor="domain-purpose">Application</label><select id="domain-purpose" value={domainPurpose} onChange={(event) => setDomainPurpose(event.target.value as "STOREFRONT" | "TENANT_ADMIN")}><option value="STOREFRONT">Customer storefront</option><option value="TENANT_ADMIN">Tenant Admin</option></select><label htmlFor="domain-hostname">Local hostname</label><div><input id="domain-hostname" value={domainHostname} onChange={(event) => setDomainHostname(event.target.value.toLowerCase())} placeholder={domainPurpose === "STOREFRONT" ? "lifemac.localhost" : "admin.lifemac.localhost"} required pattern="(?:localhost|[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.localhost)"/><button className="primary-button" disabled={domainSaving || tenants.find((tenant) => tenant.id === selectedDomainTenant)?.status === "DELETION_REQUESTED"}><Icon name="plus"/>Register</button></div><small>Enter only a local hostname—without http:// or a port. A tenant can have one verified hostname for each application.</small></form>
          <div className="domain-list">{domainLoading ? <div className="domain-loading">Loading domains...</div> : domains.map((domain) => <article className="domain-card" key={domain.id}><span className={`domain-state ${domain.verification_status === "VERIFIED" ? "verified" : "pending"}`}><Icon name={domain.verification_status === "VERIFIED" ? "shield" : "domain"}/></span><div><strong>{domain.hostname}</strong><small>{domain.purpose === "STOREFRONT" ? "Customer storefront" : "Tenant Admin"} · {domain.verification_method} verification · {domain.verification_status === "VERIFIED" ? `Verified ${new Intl.DateTimeFormat("en", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(domain.verified_at!))}` : "Awaiting verification"}</small></div><span className={`verification-pill ${domain.verification_status === "VERIFIED" ? "verified" : "pending"}`}>{domain.verification_status === "VERIFIED" ? "Verified" : "Pending"}</span>{domain.verification_status !== "VERIFIED" && <button className="secondary-button compact" type="button" disabled={domainSaving} onClick={() => void verifyDomain(domain)}>Verify</button>}</article>)}{domains.length === 0 && <div className="empty-state compact-empty"><span><Icon name="domain" size={24}/></span><h3>No hostname registered</h3><p>Register the storefront hostname before starting provisioning.</p></div>}</div>
        </> : <div className="empty-state"><span><Icon name="domain" size={24}/></span><h3>Select a tenant</h3><p>Choose a tenant to manage its local routing hostname.</p></div>}
      </section>}

      {view === "tenants" && <section className="registry-card">
        <div className="registry-toolbar">
          <div className="search-box"><Icon name="search"/><input aria-label="Search tenants" placeholder="Search by name or tenant ID" value={search} onChange={(event) => setSearch(event.target.value)}/></div>
          <div className="filter-group" aria-label="Filter tenants">
            {(["ALL", "PENDING", "PROVISIONING", "FAILED", "DELETION_REQUESTED"] as const).map((value) => {
              const labels = { ALL: "All", PENDING: "Pending", PROVISIONING: "Provisioning", FAILED: "Failed", DELETION_REQUESTED: "Deletion" };
              return <button key={value} className={filter === value ? "selected" : ""} onClick={() => setFilter(value)}>{labels[value]}</button>;
            })}
          </div>
          <button className="icon-button" aria-label="Refresh tenant registry" title="Refresh" onClick={() => loadTenants(true)} disabled={loading}><Icon name="refresh"/></button>
        </div>

        <div className="table-wrap">
          <table>
            <thead><tr><th>Tenant</th><th>Status</th><th>Created</th><th>Tenant ID</th><th><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>
              {loading && tenants.length === 0 ? Array.from({ length: 3 }).map((_, index) => <tr className="skeleton-row" key={index}><td><span/></td><td><span/></td><td><span/></td><td><span/></td><td/></tr>) : visibleTenants.map((tenant) => <tr key={tenant.id}>
                <td data-label="Tenant"><div className="tenant-cell"><span className="tenant-logo">{tenant.display_name.slice(0, 2).toUpperCase()}</span><div><strong>{tenant.display_name}</strong><small className={tenant.initial_owner_email ? "" : "owner-missing"}>{tenant.initial_owner_email ?? "Initial administrator required"}</small></div></div></td>
                <td data-label="Status"><StatusPill status={tenant.status}/></td>
                <td data-label="Created"><span className="date-value">{new Intl.DateTimeFormat("en", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(tenant.created_at))}</span></td>
                <td data-label="Tenant ID"><button className="copy-id" title="Copy tenant ID" onClick={() => { void navigator.clipboard.writeText(tenant.id); setNotice({ tone: "info", message: "Tenant ID copied" }); }}><code>{tenant.id.slice(0, 8)}...{tenant.id.slice(-4)}</code><Icon name="copy" size={14}/></button></td>
                <td className="actions"><button className="secondary-button compact" disabled={tenant.status === "DELETION_REQUESTED"} title="Set initial tenant administrator" onClick={() => openOwnerContact(tenant)}><Icon name="tenants" size={15}/><span>Owner</span></button><button className="secondary-button compact" title="Edit tenant branding" onClick={() => void openBranding(tenant)}><Icon name="shield" size={15}/><span>Branding</span></button><button className="secondary-button compact" disabled={tenant.status === "DELETION_REQUESTED"} title="Manage tenant domains" onClick={() => openDomains(tenant)}><Icon name="domain" size={15}/><span>Domain</span></button><button className="secondary-button compact" disabled={tenant.status !== "PENDING" || !tenant.initial_owner_email} title={!tenant.initial_owner_email ? "Add the initial administrator before provisioning" : "Start tenant provisioning"} onClick={() => setProvisionTarget(tenant)}><Icon name="grid" size={15}/><span>Provision</span></button><button className="danger-action" disabled={tenant.status !== "PENDING"} title={tenant.status === "PENDING" ? "Request tenant deletion" : tenant.status === "DELETION_REQUESTED" ? "Deletion already requested" : "Final offboarding requires the protected retention workflow"} onClick={() => openDelete(tenant)}><Icon name="trash" size={16}/><span>Request deletion</span></button></td>
              </tr>)}
            </tbody>
          </table>
          {!loading && visibleTenants.length === 0 && <div className="empty-state"><span><Icon name="search" size={24}/></span><h3>No tenants found</h3><p>{tenants.length ? "Try another search or status filter." : "Create your first tenant to begin onboarding."}</p>{!tenants.length && <button className="text-button" onClick={() => setCreateOpen(true)}>Create a tenant <Icon name="arrow" size={16}/></button>}</div>}
        </div>
        <footer className="table-footer"><span>Showing {visibleTenants.length} of {tenants.length} tenants</span><span>Registry updates are audited</span></footer>
      </section>}
    </main>

    {createOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setCreateOpen(false); }}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="create-title">
        <button className="modal-close" aria-label="Close" onClick={() => setCreateOpen(false)}><Icon name="close"/></button>
        <span className="modal-icon create"><Icon name="plus" size={24}/></span><p className="overline">Tenant onboarding</p><h2 id="create-title">Add a business</h2><p>Create the registry record now. Provisioning and domain verification happen in later workflow steps.</p>
        <form onSubmit={createTenant}><label htmlFor="tenant-name">Business name</label><input id="tenant-name" autoFocus value={name} onChange={(event) => { const nextName = event.target.value; setBrandName((current) => !current || current === name ? nextName : current); setName(nextName); }} minLength={1} maxLength={200} placeholder="e.g. Northstar Pharmacy Private Limited" required/><label htmlFor="owner-email">Initial tenant administrator</label><input id="owner-email" type="email" value={ownerEmail} onChange={(event) => setOwnerEmail(event.target.value)} maxLength={320} autoComplete="email" placeholder="e.g. owner@northstar.example" aria-describedby="owner-email-hint" required/><p className="field-hint" id="owner-email-hint">Create this exact verified email in Keycloak for local sign-in. No invitation email is sent yet.</p><label htmlFor="brand-name">Customer-facing display name</label><input id="brand-name" value={brandName} onChange={(event) => setBrandName(event.target.value)} minLength={1} maxLength={120} placeholder="e.g. Northstar Pharmacy" required/><label htmlFor="brand-initials">Fallback initials <small>Optional — generated automatically</small></label><input id="brand-initials" value={initials} onChange={(event) => setInitials(event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 4))} maxLength={4} placeholder="e.g. NP"/><fieldset className="theme-fieldset"><legend>Store theme</legend><p>One consistent light theme will be used across this tenant’s applications.</p><div className="theme-grid">{themes.map((theme) => <button className={`theme-card ${themeKey === theme.key ? "selected" : ""}`} type="button" key={theme.key} onClick={() => setThemeKey(theme.key)} aria-pressed={themeKey === theme.key}><span className="theme-preview" style={{ background: theme.surface }}><i style={{ background: theme.primary }}/><i style={{ background: theme.primary_dark }}/><i style={{ background: theme.accent }}/></span><strong>{theme.name}</strong>{themeKey === theme.key && <em>Selected</em>}</button>)}</div></fieldset><div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancel</button><button className="primary-button" disabled={creating || themes.length !== 5}>{creating ? "Creating..." : "Create tenant"}</button></div></form>
      </section>
    </div>}

    {brandingTarget && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setBrandingTarget(null); }}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="branding-title"><button className="modal-close" aria-label="Close" onClick={() => setBrandingTarget(null)}><Icon name="close"/></button><span className="modal-icon create"><Icon name="shield" size={24}/></span><p className="overline">Tenant identity</p><h2 id="branding-title">Edit branding</h2><p>Changes are stored centrally and will be consumed by this tenant’s shared applications.</p><form onSubmit={saveBranding}><label htmlFor="edit-brand-name">Display name</label><input id="edit-brand-name" value={brandName} onChange={(event) => setBrandName(event.target.value)} required maxLength={120}/><label htmlFor="edit-initials">Fallback initials</label><input id="edit-initials" value={initials} onChange={(event) => setInitials(event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 4))} maxLength={4}/><fieldset className="theme-fieldset"><legend>Store theme</legend><p>A single consistent light theme is applied. No dark/light mode switch is created.</p><div className="theme-grid">{themes.map((theme) => <button className={`theme-card ${themeKey === theme.key ? "selected" : ""}`} type="button" key={theme.key} onClick={() => setThemeKey(theme.key)} aria-pressed={themeKey === theme.key}><span className="theme-preview" style={{ background: theme.surface }}><i style={{ background: theme.primary }}/><i style={{ background: theme.primary_dark }}/><i style={{ background: theme.accent }}/></span><strong>{theme.name}</strong>{themeKey === theme.key && <em>Selected</em>}</button>)}</div></fieldset><div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setBrandingTarget(null)}>Cancel</button><button className="primary-button" disabled={brandingSaving}>{brandingSaving ? "Saving..." : "Save branding"}</button></div></form></section></div>}

    {contactTarget && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setContactTarget(null); }}><section className="modal contact-modal" role="dialog" aria-modal="true" aria-labelledby="contact-title"><button className="modal-close" aria-label="Close" onClick={() => setContactTarget(null)}><Icon name="close"/></button><span className="modal-icon create"><Icon name="tenants" size={24}/></span><p className="overline">Identity bootstrap</p><h2 id="contact-title">Initial administrator</h2><p>This email must exactly match the verified Keycloak user who will first enter this tenant’s administration workspace.</p><form onSubmit={saveOwnerContact}><div className="tenant-context"><strong>{contactTarget.display_name}</strong><span>{contactTarget.id}</span></div><label htmlFor="contact-email">Administrator email</label><input id="contact-email" type="email" autoFocus value={contactEmail} onChange={(event) => setContactEmail(event.target.value)} maxLength={320} autoComplete="email" required/><p className="field-hint">Updating this contact does not create a Keycloak account, password or membership by itself.</p><div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setContactTarget(null)}>Cancel</button><button className="primary-button" disabled={contactSaving}>{contactSaving ? "Saving..." : "Save administrator"}</button></div></form></section></div>}

    {deleteTarget && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setDeleteTarget(null); }}>
      <section className="modal danger-modal" role="dialog" aria-modal="true" aria-labelledby="delete-title">
        <button className="modal-close" aria-label="Close" onClick={() => setDeleteTarget(null)}><Icon name="close"/></button>
        <span className="modal-icon danger"><Icon name="trash" size={23}/></span><p className="overline danger-text">Protected action</p><h2 id="delete-title">Request tenant deletion?</h2><p>This begins an audited offboarding request. It does not erase databases or bypass retention review.</p>
        <div className="warning-box"><strong>{deleteTarget.display_name}</strong><span>{deleteTarget.id}</span></div>
        <label htmlFor="confirm-name">Type <strong>{deleteTarget.display_name}</strong> to confirm</label><input id="confirm-name" autoFocus value={confirmName} onChange={(event) => setConfirmName(event.target.value)} autoComplete="off"/>
        <div className="modal-actions"><button className="secondary-button" onClick={() => setDeleteTarget(null)}>Cancel</button><button className="danger-button" disabled={deleting || confirmName.trim() !== deleteTarget.display_name} onClick={requestDeletion}>{deleting ? "Requesting..." : "Request deletion"}</button></div>
      </section>
    </div>}

    {provisionTarget && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setProvisionTarget(null); }}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="provision-title">
        <button className="modal-close" aria-label="Close" onClick={() => setProvisionTarget(null)}><Icon name="close"/></button>
        <span className="modal-icon create"><Icon name="grid" size={24}/></span><p className="overline">Tenant provisioning</p><h2 id="provision-title">Prepare {provisionTarget.display_name}</h2>
        <p>Choose the services to prepare. Each service receives its own schema inside one tenant database.</p>
        {(["identity_access", "catalogue_fixture", "inventory_fixture", "media_fixture"] as const).map((service) => <label className="service-option" key={service}><input type="checkbox" checked={provisionServices.includes(service)} onChange={() => setProvisionServices((current) => current.includes(service) ? current.filter((item) => item !== service) : [...current, service])}/><span><strong>{servicePresentation[service].name}</strong><small>{servicePresentation[service].description}</small></span></label>)}
        <div className="modal-actions"><button className="secondary-button" onClick={() => setProvisionTarget(null)}>Cancel</button><button className="primary-button" disabled={provisioning || provisionServices.length === 0} onClick={startProvisioning}>{provisioning ? "Starting..." : "Start provisioning"}</button></div>
      </section>
    </div>}
  </div>;
}
