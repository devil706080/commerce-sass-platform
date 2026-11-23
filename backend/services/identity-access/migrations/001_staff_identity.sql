CREATE TABLE IF NOT EXISTS {schema}.identity_schema_migrations (
    version integer PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.identity_principals (
    id uuid PRIMARY KEY,
    issuer text NOT NULL,
    subject text NOT NULL,
    email varchar(320) NOT NULL,
    display_name varchar(200),
    created_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_identity_principal_subject UNIQUE (issuer, subject)
);

CREATE TABLE IF NOT EXISTS {schema}.staff_invitations (
    id uuid PRIMARY KEY,
    email varchar(320) NOT NULL,
    role varchar(32) NOT NULL,
    status varchar(16) NOT NULL DEFAULT 'PENDING',
    invited_by_issuer text NOT NULL,
    invited_by_subject text NOT NULL,
    expires_at timestamptz NOT NULL DEFAULT (now() + interval '7 days'),
    created_at timestamptz NOT NULL DEFAULT now(),
    accepted_at timestamptz,
    CONSTRAINT ck_staff_invitation_role CHECK (
        role IN ('TENANT_OWNER','TENANT_ADMIN','CATALOGUE_MANAGER','ORDER_MANAGER','VIEWER')
    ),
    CONSTRAINT ck_staff_invitation_status CHECK (
        status IN ('PENDING','ACCEPTED','REVOKED','EXPIRED')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_staff_invitation_email
ON {schema}.staff_invitations (lower(email)) WHERE status = 'PENDING';

CREATE TABLE IF NOT EXISTS {schema}.staff_memberships (
    id uuid PRIMARY KEY,
    principal_id uuid NOT NULL REFERENCES {schema}.identity_principals(id) ON DELETE CASCADE,
    role varchar(32) NOT NULL,
    status varchar(16) NOT NULL DEFAULT 'ACTIVE',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_staff_membership_principal UNIQUE (principal_id),
    CONSTRAINT ck_staff_membership_role CHECK (
        role IN ('TENANT_OWNER','TENANT_ADMIN','CATALOGUE_MANAGER','ORDER_MANAGER','VIEWER')
    ),
    CONSTRAINT ck_staff_membership_status CHECK (
        status IN ('ACTIVE','SUSPENDED','REVOKED')
    )
);

REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE ON {schema}.identity_principals TO {runtime_role};
GRANT SELECT, INSERT, UPDATE ON {schema}.staff_invitations TO {runtime_role};
GRANT SELECT, INSERT, UPDATE ON {schema}.staff_memberships TO {runtime_role};
GRANT SELECT ON {schema}.identity_schema_migrations TO {runtime_role};
ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE ALL ON TABLES FROM PUBLIC;

INSERT INTO {schema}.identity_schema_migrations(version) VALUES (1)
ON CONFLICT (version) DO NOTHING;
