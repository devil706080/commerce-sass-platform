import { NextRequest } from "next/server";

const services = {
  identity: { key: "identity_access", url: process.env.IDENTITY_API_INTERNAL_URL },
  catalogue: { key: "catalogue_fixture", url: process.env.CATALOGUE_API_INTERNAL_URL },
  inventory: { key: "inventory_fixture", url: process.env.INVENTORY_API_INTERNAL_URL },
  media: { key: "media_fixture", url: process.env.MEDIA_API_INTERNAL_URL },
} as const;

async function proxy(request: NextRequest, context: { params: Promise<{ service: string; path: string[] }> }) {
  const { service, path } = await context.params;
  const target = services[service as keyof typeof services];
  const controlPlane = process.env.CONTROL_PLANE_INTERNAL_URL;
  const brokerToken = process.env.TENANT_CONTEXT_BROKER_TOKEN;
  const host = request.headers.get("host");
  if (!target?.url || !controlPlane || !brokerToken || !host) {
    return Response.json({ detail: "Tenant service routing is unavailable" }, { status: 503 });
  }
  const contextResponse = await fetch(
    `${controlPlane}/_internal/tenant-context?service_key=${encodeURIComponent(target.key)}`,
    { method: "POST", headers: { Authorization: `Bearer ${brokerToken}`, "X-Forwarded-Host": host }, cache: "no-store" },
  );
  if (!contextResponse.ok) {
    return Response.json({ detail: "Tenant service is unavailable for this domain" }, { status: contextResponse.status });
  }
  const issued = await contextResponse.json() as { token: string };
  const targetUrl = new URL(`${target.url}/${path.map(encodeURIComponent).join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => targetUrl.searchParams.append(key, value));
  const headers = new Headers();
  const authorization = request.headers.get("authorization");
  const contentType = request.headers.get("content-type");
  if (authorization) headers.set("authorization", authorization);
  if (service !== "identity") {
    if (!authorization || !services.identity.url) {
      return Response.json({ detail: "Authentication is required" }, { status: 401 });
    }
    const identityContextResponse = await fetch(
      `${controlPlane}/_internal/tenant-context?service_key=identity_access`,
      { method: "POST", headers: { Authorization: `Bearer ${brokerToken}`, "X-Forwarded-Host": host }, cache: "no-store" },
    );
    if (!identityContextResponse.ok) return Response.json({ detail: "Tenant membership is unavailable" }, { status: 403 });
    const identityContext = await identityContextResponse.json() as { token: string };
    const membership = await fetch(`${services.identity.url}/api/v1/me`, {
      headers: { Authorization: authorization, "X-Tenant-Context": identityContext.token },
      cache: "no-store",
    });
    if (!membership.ok) return Response.json({ detail: "Tenant membership is unavailable" }, { status: membership.status === 401 ? 401 : 403 });
  }
  if (contentType) headers.set("content-type", contentType);
  headers.set("x-tenant-context", issued.token);
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer();
  const response = await fetch(targetUrl, { method: request.method, headers, body, cache: "no-store" });
  return new Response(response.body, { status: response.status, headers: { "content-type": response.headers.get("content-type") ?? "application/json" } });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
