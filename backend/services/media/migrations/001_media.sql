CREATE TABLE IF NOT EXISTS {schema}.assets (
    id uuid PRIMARY KEY,
    original_filename text NOT NULL,
    content_type text NOT NULL CHECK (content_type = 'image/webp'),
    byte_size integer NOT NULL CHECK (byte_size > 0),
    width integer NOT NULL CHECK (width > 0),
    height integer NOT NULL CHECK (height > 0),
    storage_key text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);
