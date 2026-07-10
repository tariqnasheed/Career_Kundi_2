# CareerKundi geo / jurisdiction / locale domain (0050-PF6-S1)

## Owns

- `GeoRef` / `JurisdictionRef` / `LocaleRef` / `WorkAuthorizationAreaRef`
- Controlled kind enums
- Storage stubs: `geo_areas`, `jurisdiction_areas`, `locale_profiles`, `work_authorization_areas`
- Create/get service helpers

## Does not own

- Visa rules / candidate authorization status
- Tax / employment-law engines
- Global country/city imports / CLDR
- Localization translation strings
- Public FastAPI geo API
- Cross-domain FKs (jurisdiction↔geo, locale↔geo, auth↔geo)

## Semantics

| Concept | Meaning |
|---------|---------|
| Geography | Where something physically/logistically is |
| Jurisdiction | Which legal/regulatory authority applies |
| Locale | Presentation/language/format preference |
| Work authorization area | Future legal work-authorization area (not status) |

**Geography ≠ jurisdiction ≠ locale ≠ work-authorization status.**
No helper auto-cross-links these domains.
