from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from identity_access.config.settings import Settings
from identity_access.domain.models import (
    AuthenticatedIdentity,
    Membership,
    MembershipStatus,
    StaffRole,
)


class OwnerBootstrapConflict(Exception):
    """The first-owner bootstrap was completed or claimed by another email."""


class IdentityRepository:
    def __init__(self, settings: Settings):
        self.settings = settings

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        with psycopg.connect(self.settings.database_url(), row_factory=dict_row) as connection:
            connection.execute(
                sql.SQL("SET search_path TO {}, public").format(
                    sql.Identifier(self.settings.schema_name)
                )
            )
            yield connection

    def create_invitation(
        self,
        email: str,
        role: StaffRole,
        actor: AuthenticatedIdentity,
    ) -> dict[str, Any]:
        with self.connection() as connection:
            if "platform-operator" in actor.realm_roles and role == StaffRole.TENANT_OWNER:
                connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    ("identity-owner-bootstrap",),
                )
                bootstrap = connection.execute(
                    "SELECT "
                    "EXISTS (SELECT 1 FROM staff_memberships "
                    "WHERE role='TENANT_OWNER' AND status='ACTIVE') AS has_owner, "
                    "(SELECT lower(email) FROM staff_invitations WHERE role='TENANT_OWNER' "
                    "AND status='PENDING' AND expires_at > now() ORDER BY created_at LIMIT 1) "
                    "AS pending_email"
                ).fetchone()
                if bootstrap and (
                    bootstrap["has_owner"]
                    or bootstrap["pending_email"] not in {None, email.casefold()}
                ):
                    raise OwnerBootstrapConflict
            connection.execute(
                "UPDATE staff_invitations SET status='EXPIRED' "
                "WHERE status='PENDING' AND expires_at <= now()"
            )
            existing = connection.execute(
                "SELECT id,email,role,status,expires_at,created_at,accepted_at "
                "FROM staff_invitations WHERE email=%s AND status='PENDING' "
                "AND expires_at > now()",
                (email,),
            ).fetchone()
            if existing:
                return existing
            created = connection.execute(
                "INSERT INTO staff_invitations "
                "(id,email,role,invited_by_issuer,invited_by_subject) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING "
                "RETURNING id,email,role,status,expires_at,created_at,accepted_at",
                (uuid4(), email, role.value, actor.issuer, actor.subject),
            ).fetchone()
            if created is None:
                created = connection.execute(
                    "SELECT id,email,role,status,expires_at,created_at,accepted_at "
                    "FROM staff_invitations WHERE email=%s AND status='PENDING' "
                    "AND expires_at > now()",
                    (email,),
                ).fetchone()
            if created is None:
                raise RuntimeError("invitation could not be created")
            return created

    def accept_invitation(self, identity: AuthenticatedIdentity) -> Membership | None:
        with self.connection() as connection:
            invitation = connection.execute(
                "SELECT id,role FROM staff_invitations WHERE email=%s AND status='PENDING' "
                "AND expires_at > now() FOR UPDATE",
                (identity.email,),
            ).fetchone()
            if not invitation:
                row = self._find_membership(connection, identity)
                return self._membership(row) if row else None
            principal = connection.execute(
                "INSERT INTO identity_principals "
                "(id,issuer,subject,email,display_name) VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (issuer,subject) DO UPDATE SET email=EXCLUDED.email, "
                "display_name=EXCLUDED.display_name,last_seen_at=now() "
                "RETURNING id",
                (uuid4(), identity.issuer, identity.subject, identity.email, identity.display_name),
            ).fetchone()
            if principal is None:
                raise RuntimeError("principal upsert returned no row")
            membership = connection.execute(
                "INSERT INTO staff_memberships (id,principal_id,role) VALUES (%s,%s,%s) "
                "ON CONFLICT (principal_id) DO UPDATE SET role=EXCLUDED.role,status='ACTIVE',updated_at=now() "
                "RETURNING id,principal_id,role,status",
                (uuid4(), principal["id"], invitation["role"]),
            ).fetchone()
            if membership is None:
                raise RuntimeError("membership upsert returned no row")
            connection.execute(
                "UPDATE staff_invitations SET status='ACCEPTED',accepted_at=now() WHERE id=%s",
                (invitation["id"],),
            )
            return Membership(
                id=membership["id"],
                principal_id=membership["principal_id"],
                email=identity.email,
                display_name=identity.display_name,
                role=StaffRole(membership["role"]),
                status=MembershipStatus(membership["status"]),
            )

    def find_membership(self, identity: AuthenticatedIdentity) -> Membership | None:
        with self.connection() as connection:
            row = self._find_membership(connection, identity)
        if not row:
            return None
        return self._membership(row)

    def bootstrap_owner(self, identity: AuthenticatedIdentity) -> Membership:
        with self.connection() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                ("identity-owner-bootstrap",),
            )
            existing_owner = connection.execute(
                "SELECT 1 FROM staff_memberships "
                "WHERE role='TENANT_OWNER' AND status='ACTIVE' LIMIT 1"
            ).fetchone()
            if existing_owner:
                existing = self._find_membership(connection, identity)
                if existing:
                    return self._membership(existing)
                raise OwnerBootstrapConflict
            principal = connection.execute(
                "INSERT INTO identity_principals "
                "(id,issuer,subject,email,display_name) VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (issuer,subject) DO UPDATE SET email=EXCLUDED.email, "
                "display_name=EXCLUDED.display_name,last_seen_at=now() RETURNING id",
                (uuid4(), identity.issuer, identity.subject, identity.email, identity.display_name),
            ).fetchone()
            if principal is None:
                raise RuntimeError("principal upsert returned no row")
            row = connection.execute(
                "INSERT INTO staff_memberships (id,principal_id,role,status) "
                "VALUES (%s,%s,'TENANT_OWNER','ACTIVE') "
                "ON CONFLICT (principal_id) DO UPDATE SET role='TENANT_OWNER',"
                "status='ACTIVE',updated_at=now() "
                "RETURNING id,principal_id,role,status",
                (uuid4(), principal["id"]),
            ).fetchone()
            if row is None:
                raise RuntimeError("owner membership upsert returned no row")
            return Membership(
                id=row["id"],
                principal_id=row["principal_id"],
                email=identity.email,
                display_name=identity.display_name,
                role=StaffRole(row["role"]),
                status=MembershipStatus(row["status"]),
            )

    @staticmethod
    def _find_membership(
        connection: psycopg.Connection[dict[str, Any]], identity: AuthenticatedIdentity
    ) -> dict[str, Any] | None:
        return connection.execute(
            "SELECT m.id,m.principal_id,p.email,p.display_name,m.role,m.status "
            "FROM identity_principals p JOIN staff_memberships m ON m.principal_id=p.id "
            "WHERE p.issuer=%s AND p.subject=%s",
            (identity.issuer, identity.subject),
        ).fetchone()

    @staticmethod
    def _membership(row: dict[str, Any]) -> Membership:
        return Membership(
            id=row["id"],
            principal_id=row["principal_id"],
            email=row["email"],
            display_name=row["display_name"],
            role=StaffRole(row["role"]),
            status=MembershipStatus(row["status"]),
        )

    def list_memberships(self) -> list[Membership]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT m.id,m.principal_id,p.email,p.display_name,m.role,m.status "
                "FROM staff_memberships m JOIN identity_principals p ON p.id=m.principal_id "
                "ORDER BY p.email"
            ).fetchall()
        return [
            Membership(
                id=row["id"],
                principal_id=row["principal_id"],
                email=row["email"],
                display_name=row["display_name"],
                role=StaffRole(row["role"]),
                status=MembershipStatus(row["status"]),
            )
            for row in rows
        ]

    def can_bootstrap_owner(self, email: str) -> bool:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT "
                "EXISTS (SELECT 1 FROM staff_memberships "
                "WHERE role='TENANT_OWNER' AND status='ACTIVE') AS has_owner, "
                "(SELECT lower(email) FROM staff_invitations WHERE role='TENANT_OWNER' "
                "AND status='PENDING' AND expires_at > now() ORDER BY created_at LIMIT 1) "
                "AS pending_email"
            ).fetchone()
            if not row or row["has_owner"]:
                return False
            return row["pending_email"] in {None, email.casefold()}
