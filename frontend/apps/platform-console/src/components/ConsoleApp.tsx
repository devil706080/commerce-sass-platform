"use client";

import Keycloak from "keycloak-js";
import { FormEvent, useEffect, useRef, useState } from "react";

type Tenant = { id: string; display_name: string; status: "PENDING"; created_at: string };

const keycloak = new Keycloak({
  url: process.env.NEXT_PUBLIC_KEYCLOAK_URL!,
  realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM!,
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID!,
});
const api = process.env.NEXT_PUBLIC_CONTROL_API_URL!;

export default function ConsoleApp() {
  const initialized = useRef(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [name, setName] = useState("");
  const [message, setMessage] = useState("Checking your session…");

  async function request(path: string, init?: RequestInit) {
    await keycloak.updateToken(30);
    return fetch(`${api}${path}`, {
      ...init,
      headers: { Authorization: `Bearer ${keycloak.token}`, "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  }

  async function loadTenants() {
    const response = await request("/api/v1/tenants");
    if (!response.ok) throw new Error(`Tenant request failed (${response.status})`);
    setTenants(await response.json());
  }

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;
    keycloak.init({ onLoad: "check-sso", pkceMethod: "S256", checkLoginIframe: false })
      .then(async (ok) => {
        setAuthenticated(ok);
        setMessage(ok ? "Authenticated platform operator" : "Sign in to manage tenants");
        if (ok) await loadTenants();
      })
      .catch(() => setMessage("Authentication service is unavailable"));
  }, []);

  async function createTenant(event: FormEvent) {
    event.preventDefault();
    const response = await request("/api/v1/tenants", {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({ display_name: name }),
    });
    const body = await response.json();
    if (!response.ok) { setMessage(body.detail ?? "Unable to create tenant"); return; }
    setName("");
    setMessage(`${body.display_name} created with PENDING status`);
    await loadTenants();
  }

  if (!authenticated) return (
    <main className="shell"><section className="login-card"><span className="eyebrow">Commerce SaaS</span>
      <h1>Platform operations</h1><p>{message}</p>
      <button onClick={() => keycloak.login({ redirectUri: window.location.origin })}>Sign in securely</button>
    </section></main>
  );

  return <main className="dashboard">
    <header><div><span className="eyebrow">Commerce SaaS</span><h1>Tenant control plane</h1><p>{message}</p></div>
      <button className="secondary" onClick={() => keycloak.logout({ redirectUri: window.location.origin })}>Sign out</button></header>
    <section className="grid"><form className="panel" onSubmit={createTenant}><h2>Onboard a tenant</h2>
      <label htmlFor="name">Business display name</label><input id="name" value={name} onChange={(e) => setName(e.target.value)} minLength={1} maxLength={200} required />
      <button type="submit">Create pending tenant</button><small>New tenants remain pending until verification and provisioning finish.</small></form>
      <section className="panel"><div className="section-title"><h2>Tenant registry</h2><span>{tenants.length} records</span></div>
        {tenants.length === 0 ? <p className="empty">No tenants yet.</p> : <div className="list">{tenants.map((tenant) => <article key={tenant.id}><div><strong>{tenant.display_name}</strong><code>{tenant.id}</code></div><span className="status">{tenant.status}</span></article>)}</div>}
      </section></section>
  </main>;
}
