CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    uuid            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   TEXT            NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted         BOOLEAN         NOT NULL DEFAULT FALSE
);

CREATE TABLE refresh_tokens (
    id              SERIAL PRIMARY KEY,
    user_uuid       UUID            NOT NULL REFERENCES users(uuid),
    marketplace     VARCHAR(255)    NOT NULL,
    refresh_token   TEXT            NOT NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMPTZ     NOT NULL,
);
