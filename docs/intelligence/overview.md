# Intelligence System Overview

The intelligence system is a background worker that:

- Fetches weather and zone data
- Computes fire risk metrics
- Persists periodic and instant risk readings
- Publishes Redis events consumed by backend streaming

The API reference page is generated from modules in `intelligence-system/src`.
