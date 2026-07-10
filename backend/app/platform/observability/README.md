# CareerKundi observability domain (0050-PF10-S1)

## Owns

- Request correlation ID helpers (`X-Request-ID`)
- Privacy-aware redaction helpers
- Safe `ObservabilityEvent` primitives
- Structured logging helpers for those events
- Minimal request timing / completion middleware

## Does not own

- OpenTelemetry exporters or collectors
- Vendor SDKs (Datadog, Sentry, New Relic, Honeycomb, Grafana Cloud)
- Alerting, dashboards, or log shipping infrastructure
- Database-backed audit / compliance logging
- Frontend observability UI

## Semantics

| Concept | Meaning |
|---------|---------|
| Correlation ID | Opaque request connector for logs — not auth or identity |
| Redaction | Strip known sensitive keys from log/event attributes |
| Observability event | Operational metadata event — not a legal audit record |
| Middleware | Normalize ID, time request, log safe completion metadata |

**Log metadata, not user content.**

These primitives support future operational observability.
They are not a compliance audit trail and do not by themselves make CareerKundi legally compliant.
