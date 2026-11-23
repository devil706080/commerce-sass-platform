import json
import os
import time
from string import Formatter
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _json_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: object | None = None,
):
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=encoded, method=method, headers=headers or {})
    if encoded is not None:
        request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=10) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def _admin_token(base_url: str, username: str, password: str) -> str:
    payload = urlencode(
        {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": username,
            "password": password,
        }
    ).encode("utf-8")
    request = Request(
        f"{base_url}/realms/master/protocol/openid-connect/token",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read())["access_token"]


def _origin(template: str, hostname: str) -> str:
    fields = {field for _, field, _, _ in Formatter().parse(template) if field}
    if fields != {"hostname"}:
        raise RuntimeError("TENANT_ADMIN_ORIGIN_TEMPLATE must contain only {hostname}")
    return template.format(hostname=hostname).rstrip("/")


def synchronize() -> int:
    keycloak_url = _required("KEYCLOAK_INTERNAL_URL").rstrip("/")
    control_url = _required("CONTROL_PLANE_INTERNAL_URL").rstrip("/")
    realm = _required("KEYCLOAK_REALM")
    client_id = _required("KEYCLOAK_TENANT_ADMIN_CLIENT_ID")
    template = _required("TENANT_ADMIN_ORIGIN_TEMPLATE")
    broker = _required("TENANT_CONTEXT_BROKER_TOKEN")
    username = _required("KEYCLOAK_ADMIN_USERNAME")
    password = _required("KEYCLOAK_ADMIN_PASSWORD")

    domains = _json_request(
        f"{control_url}/_internal/tenant-admin-domains",
        headers={"Authorization": f"Bearer {broker}"},
    )["hostnames"]
    token = _admin_token(keycloak_url, username, password)
    headers = {"Authorization": f"Bearer {token}"}
    clients = _json_request(
        f"{keycloak_url}/admin/realms/{realm}/clients?clientId={client_id}", headers=headers
    )
    if len(clients) != 1:
        raise RuntimeError("tenant-admin Keycloak client was not found uniquely")
    client_uuid = clients[0]["id"]
    client = _json_request(
        f"{keycloak_url}/admin/realms/{realm}/clients/{client_uuid}", headers=headers
    )
    configured_origins = {_origin(template, hostname) for hostname in domains}
    bootstrap_origins = {
        origin.rstrip("/")
        for origin in os.getenv("TENANT_ADMIN_BOOTSTRAP_ORIGINS", "").split(",")
        if origin.strip()
    }
    origins = sorted(configured_origins | bootstrap_origins)
    client["redirectUris"] = [f"{origin}/*" for origin in origins]
    client["webOrigins"] = origins
    _json_request(
        f"{keycloak_url}/admin/realms/{realm}/clients/{client_uuid}",
        method="PUT",
        headers=headers,
        body=client,
    )

    mappers = _json_request(
        f"{keycloak_url}/admin/realms/{realm}/clients/{client_uuid}/protocol-mappers/models",
        headers=headers,
    )
    for mapper in mappers:
        if mapper.get("name") == "tenant-id":
            _json_request(
                f"{keycloak_url}/admin/realms/{realm}/clients/{client_uuid}/protocol-mappers/models/{mapper['id']}",
                method="DELETE",
                headers=headers,
            )
    return len(configured_origins)


def main() -> None:
    interval = int(os.getenv("KEYCLOAK_SYNC_INTERVAL_SECONDS", "15"))
    while True:
        try:
            count = synchronize()
            print(f"Keycloak tenant-admin redirects synchronized: {count} verified domains")
        except (HTTPError, URLError, KeyError, RuntimeError, ValueError) as exc:
            print(f"Keycloak tenant-admin redirect synchronization deferred: {type(exc).__name__}")
        time.sleep(max(interval, 5))


if __name__ == "__main__":
    main()
