CREATE EXTENSION "pgcrypto";


CREATE TABLE users (
    uuid			UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255)  NOT NULL UNIQUE,
    password_hash   TEXT          NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
);
