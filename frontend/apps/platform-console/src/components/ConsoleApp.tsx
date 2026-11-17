"use client";

import Keycloak from "keycloak-js";
import { FormEvent, ReactNode, useEffect, useMemo, useRef, useState } from "react";

type TenantStatus = "PENDING" | "DELETION_REQUESTED";
type Tenant = {
  id: string;
  display_name: string;
  status: TenantStatus;
  created_at: string;
  updated_at: string;
};
type Notice = { tone: "success" | "error" | "info"; message: string } | null;

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
  return <span className={`status-pill ${status === "PENDING" ? "pending" : "deleting"}`}>
    <span className="status-dot" />{status === "PENDING" ? "Pending setup" : "Deletion requested"}
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
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"ALL" | TenantStatus>("ALL");
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Tenant | null>(null);
  const [confirmName, setConfirmName] = useState("");
  const [notice, setNotice] = useState<Notice>(null);

  const operatorName = String(keycloak.tokenParsed?.preferred_username ?? keycloak.tokenParsed?.email ?? "Platform operator");

  async function request(path: string, init?: RequestInit) {
    await keycloak.updateToken(30);
    const headers = new Headers(init?.headers);
    headers.set("Authorization", `Bearer ${keycloak.token}`);
    if (init?.body) headers.set("Content-Type", "application/json");
    return fetch(`${api}${path}`, { ...init, headers });
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

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    keycloak.init({ onLoad: "check-sso", pkceMethod: "S256", checkLoginIframe: false })
      .then(async (ok) => {
        setAuthenticated(ok);
        setAuthReady(true);
        if (ok) await loadTenants();
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
        body: JSON.stringify({ display_name: name }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to create tenant");
      setName("");
      setCreateOpen(false);
      setNotice({ tone: "success", message: `${body.display_name} was added to the registry` });
      await loadTenants();
    } catch (error) {
      setNotice({ tone: "error", message: error instanceof Error ? error.message : "Unable to create tenant" });
    } finally {
      setCreating(false);
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
        <button className="nav-item active"><Icon name="tenants"/><span>Tenants</span></button>
        <button className="nav-item" disabled><Icon name="grid"/><span>Provisioning</span><em>Soon</em></button>
        <button className="nav-item" disabled><Icon name="domain"/><span>Domains</span><em>Soon</em></button>
      </nav>
      <div className="sidebar-user">
        <span className="user-avatar">{operatorName.slice(0, 1).toUpperCase()}</span>
        <div><strong>{operatorName}</strong><span>Platform operator</span></div>
        <button aria-label="Sign out" title="Sign out" onClick={() => keycloak.logout({ redirectUri: window.location.origin })}><Icon name="logout"/></button>
      </div>
    </aside>

    <main className="content">
      <header className="page-header">
        <div><p className="overline">Control plane</p><h1>Tenant registry</h1><p>Manage businesses and track their onboarding lifecycle.</p></div>
        <button className="primary-button" onClick={() => setCreateOpen(true)}><Icon name="plus"/>New tenant</button>
      </header>

      {notice && <div className={`notice ${notice.tone}`} role="status"><span>{notice.message}</span><button aria-label="Dismiss notification" onClick={() => setNotice(null)}><Icon name="close" size={16}/></button></div>}

      <section className="metrics" aria-label="Tenant overview">
        <article><span className="metric-icon blue"><Icon name="tenants"/></span><div><p>Total tenants</p><strong>{counts.total}</strong><small>Registered businesses</small></div></article>
        <article><span className="metric-icon amber"><span className="pulse-dot"/></span><div><p>Pending setup</p><strong>{counts.pending}</strong><small>Awaiting provisioning</small></div></article>
        <article><span className="metric-icon coral"><Icon name="trash"/></span><div><p>Deletion requests</p><strong>{counts.deletion}</strong><small>Awaiting offboarding review</small></div></article>
      </section>

      <section className="registry-card">
        <div className="registry-toolbar">
          <div className="search-box"><Icon name="search"/><input aria-label="Search tenants" placeholder="Search by name or tenant ID" value={search} onChange={(event) => setSearch(event.target.value)}/></div>
          <div className="filter-group" aria-label="Filter tenants">
            {(["ALL", "PENDING", "DELETION_REQUESTED"] as const).map((value) => <button key={value} className={filter === value ? "selected" : ""} onClick={() => setFilter(value)}>{value === "ALL" ? "All" : value === "PENDING" ? "Pending" : "Deletion"}</button>)}
          </div>
          <button className="icon-button" aria-label="Refresh tenant registry" title="Refresh" onClick={() => loadTenants(true)} disabled={loading}><Icon name="refresh"/></button>
        </div>

        <div className="table-wrap">
          <table>
            <thead><tr><th>Tenant</th><th>Status</th><th>Created</th><th>Tenant ID</th><th><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>
              {loading && tenants.length === 0 ? Array.from({ length: 3 }).map((_, index) => <tr className="skeleton-row" key={index}><td><span/></td><td><span/></td><td><span/></td><td><span/></td><td/></tr>) : visibleTenants.map((tenant) => <tr key={tenant.id}>
                <td data-label="Tenant"><div className="tenant-cell"><span className="tenant-logo">{tenant.display_name.slice(0, 2).toUpperCase()}</span><div><strong>{tenant.display_name}</strong><small>Commerce tenant</small></div></div></td>
                <td data-label="Status"><StatusPill status={tenant.status}/></td>
                <td data-label="Created"><span className="date-value">{new Intl.DateTimeFormat("en", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(tenant.created_at))}</span></td>
                <td data-label="Tenant ID"><button className="copy-id" title="Copy tenant ID" onClick={() => { void navigator.clipboard.writeText(tenant.id); setNotice({ tone: "info", message: "Tenant ID copied" }); }}><code>{tenant.id.slice(0, 8)}...{tenant.id.slice(-4)}</code><Icon name="copy" size={14}/></button></td>
                <td className="actions"><button className="danger-action" disabled={tenant.status !== "PENDING"} title={tenant.status === "PENDING" ? "Request tenant deletion" : "Deletion already requested"} onClick={() => openDelete(tenant)}><Icon name="trash" size={16}/><span>Request deletion</span></button></td>
              </tr>)}
            </tbody>
          </table>
          {!loading && visibleTenants.length === 0 && <div className="empty-state"><span><Icon name="search" size={24}/></span><h3>No tenants found</h3><p>{tenants.length ? "Try another search or status filter." : "Create your first tenant to begin onboarding."}</p>{!tenants.length && <button className="text-button" onClick={() => setCreateOpen(true)}>Create a tenant <Icon name="arrow" size={16}/></button>}</div>}
        </div>
        <footer className="table-footer"><span>Showing {visibleTenants.length} of {tenants.length} tenants</span><span>Registry updates are audited</span></footer>
      </section>
    </main>

    {createOpen && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setCreateOpen(false); }}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="create-title">
        <button className="modal-close" aria-label="Close" onClick={() => setCreateOpen(false)}><Icon name="close"/></button>
        <span className="modal-icon create"><Icon name="plus" size={24}/></span><p className="overline">Tenant onboarding</p><h2 id="create-title">Add a business</h2><p>Create the registry record now. Provisioning and domain verification happen in later workflow steps.</p>
        <form onSubmit={createTenant}><label htmlFor="tenant-name">Business display name</label><input id="tenant-name" autoFocus value={name} onChange={(event) => setName(event.target.value)} minLength={1} maxLength={200} placeholder="e.g. Northstar Pharmacy" required/><div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setCreateOpen(false)}>Cancel</button><button className="primary-button" disabled={creating}>{creating ? "Creating..." : "Create tenant"}</button></div></form>
      </section>
    </div>}

    {deleteTarget && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setDeleteTarget(null); }}>
      <section className="modal danger-modal" role="dialog" aria-modal="true" aria-labelledby="delete-title">
        <button className="modal-close" aria-label="Close" onClick={() => setDeleteTarget(null)}><Icon name="close"/></button>
        <span className="modal-icon danger"><Icon name="trash" size={23}/></span><p className="overline danger-text">Protected action</p><h2 id="delete-title">Request tenant deletion?</h2><p>This begins an audited offboarding request. It does not erase databases or bypass retention review.</p>
        <div className="warning-box"><strong>{deleteTarget.display_name}</strong><span>{deleteTarget.id}</span></div>
        <label htmlFor="confirm-name">Type <strong>{deleteTarget.display_name}</strong> to confirm</label><input id="confirm-name" autoFocus value={confirmName} onChange={(event) => setConfirmName(event.target.value)} autoComplete="off"/>
        <div className="modal-actions"><button className="secondary-button" onClick={() => setDeleteTarget(null)}>Cancel</button><button className="danger-button" disabled={deleting || confirmName.trim() !== deleteTarget.display_name} onClick={requestDeletion}>{deleting ? "Requesting..." : "Request deletion"}</button></div>
      </section>
    </div>}
  </div>;
}
