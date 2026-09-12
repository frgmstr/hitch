---
name: visor-vin-api
description: "Vehicle inventory API wrapper — listings, VIN lookups, dealer data."
version: 0.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, API, Vehicle, Inventory, Listings, VIN, Dealers]
---

# Visor.vin API Skill

Thin wrapper around the [Visor.vin](https://visor.vin) vehicle inventory endpoints.  Provides
listings, per-VIN detail lookups (including price history and dealer data), and dealer info.
This skill requires a **paid** Visor.vin API key — it is not functional without one.

## Prerequisites

- A Visor.vin API key set in `.env` as `VISOR_API_KEY`.  Get one at [visor.vin](https://visor.vin).
- Personalization variables (optional but recommended for filtering):
  - `TARGET_MAKE`, `TARGET_MODEL`, `TARGET_YEARS` — restrict the listing search to your target automobile.

## Endpoints Exposed

| Method | Path | Returns |
|---|---|---|
| GET | `/listings` | Active used/CPO listings matching filters (make, model, years). |
| GET | `/listings/{id}` | Detail for a single listing: pricing history, dealer info, vehicle build. |
| POST | `/vin/decode` | VIN → decoded specs + market category. |

## Authentication

All requests send `Authorization: Bearer $VISOR_API_KEY`.  The key is read from the profile's
environment at runtime — it is never hard-coded or committed to source control.

## Output Shape (listings)

```jsonc
{
  "listing_id": {
    "vehicle": {"build": {"year": 2024, "make": "TOYOTA", "model": "4RUNNER", "trim": "Limited"}},
    "price": 47995,
    "miles": 18_300,
    "days_on_market": 22,
    "price_history": [{"changed_at": "2026-09-01T...", "price_after": 49995}],
    "dealer": {"name": "...", "city": "...", "state": "..."},
    "pricing": {"seller_total_before_taxes_and_registration_usd": 50_800}
  }
}
```

This matches the shape consumed by `automobile-value-rubric` and `automobile-report`.
