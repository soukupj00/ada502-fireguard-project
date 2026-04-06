# HiveMQ Security Bundle (Minimal)

This bundle applies a minimal hardening baseline for HiveMQ CE used by this project.

## What is enabled now

- The default `hivemq-allow-all-extension` is disabled via:
  - `intelligence-system/hivemq/extensions/hivemq-allow-all-extension/DISABLED`
- In dev (`docker-compose.yml`), HiveMQ and Redis are bound to localhost only.
- In prod (`docker-compose.prod.yml`), HiveMQ and Redis are internal-only (no direct host ports).

## Cert helper for next step (TLS)

Generate local dev certs:

```zsh
./intelligence-system/hivemq/scripts/generate-dev-certs.sh
```

Files are written to `intelligence-system/hivemq/certs/`.

## Important

This bundle intentionally avoids overriding HiveMQ `config.xml` so startup remains stable.
To fully enforce TLS/authentication, add a HiveMQ config/extension setup next.
