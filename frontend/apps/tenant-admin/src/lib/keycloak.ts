"use client";

import Keycloak from "keycloak-js";

let client: Keycloak | undefined;

export function getKeycloak(): Keycloak {
  if (!client) {
    const url = process.env.NEXT_PUBLIC_KEYCLOAK_URL;
    const realm = process.env.NEXT_PUBLIC_KEYCLOAK_REALM;
    const clientId = process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID;
    if (!url || !realm || !clientId) throw new Error("Tenant Admin authentication is not configured");
    client = new Keycloak({ url, realm, clientId });
  }
  return client;
}

export async function getAccessToken(): Promise<string> {
  const keycloak = getKeycloak();
  const refreshed = await keycloak.updateToken(30);
  if (!refreshed && !keycloak.token) throw new Error("Your session has expired");
  if (!keycloak.token) throw new Error("Authentication is required");
  return keycloak.token;
}

export function hasTenantAdminRole(): boolean {
  const roles = getKeycloak().tokenParsed?.realm_access?.roles ?? [];
  return roles.includes("tenant-admin") || roles.includes("platform-operator");
}
