CREATE TABLE IF NOT EXISTS {schema}.products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sku text NOT NULL UNIQUE,
    name text NOT NULL,
    description text,
    price_cents integer NOT NULL CHECK (price_cents >= 0),
    published boolean NOT NULL DEFAULT false
);
