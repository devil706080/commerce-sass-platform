from fastapi import Depends, Header
from catalogue.config.settings import Settings, load_settings
from catalogue.dependencies.auth import CatalogueIdentity, require_catalogue_admin
from catalogue.dependencies.tenant import resolve_tenant

def admin_context(
    host: str | None = Header(default=None, alias="Host"),
    identity: CatalogueIdentity = Depends(require_catalogue_admin),
) -> CatalogueIdentity:
    resolve_tenant(load_settings(), host, identity.tenant_id)
    return identity
