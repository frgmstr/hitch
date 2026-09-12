---
name: automobile-value-rubric
description: Price used listings off sold comps with a weighted rubric.
version: 0.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Vehicle, Pricing, Valuation, CPO]
    related_skills: [visor-vin-api, automobile-report, grounded-citations]
---

# Automobile Value Rubric

Builds fair-price lines from actual sold transactions, then scores active used listings
against them with a multi-factor weighted rubric.  This is a **generic** fork of an internal
Bronco-only pipeline — it works for any automobile once you supply a regression model and
trim/recall tables that match your target vehicle.

It does NOT invent prices when comps are missing — it says "verify listings" instead.
Stdlib Python plus any inventory API exposing sold history (Visor.vin is the reference backend).

## When to Use

- "What's a fair price for this [YEAR] [MODEL] with [N] miles?"
- A listing looks too high or too low relative to recent sold comps — flag it.
- Comparing multiple active listings on a single scored leaderboard (best value at top).

## Prerequisites / Personalization

This skill is **not** plug-and-play out of the box for an arbitrary automobile.  You must
customize three things:

1. **`value-model.json`** (copy from `value-model.example.json`) — a regression model mapping
   `"YEAR|TRIM"` to `{"a": <intercept>, "b": <slope_per_mile>}`.  This is the single most
   important personalization file; without it, fair-price scores cannot be computed.

2. **Trim / expected-mileage tables** in `scripts/rubric-score.py` — the `ppm_by_trim`,
   `exp_mi`, and `RECALLS`/`DND` dictionaries are pre-filled with example values for a
   mid-size SUV.  Replace them with values that match your target automobile (see comments
   marked `# >>> PERSONALIZE <<<`).

3. **Visor.vin API key** — set `VISOR_API_KEY` in `.env`.  Without it, no live data is pulled;
   the rubric can still run against a pre-cached `visor_details_cpo_active.json`, but that file
   must come from somewhere (manual scrape or another tool).

## Input / Output Files

All paths are resolved relative to `ARCH = $HERMES_ARCHIVE_DIR` (default `./archives`):

| File | Role | Source |
|---|---|---|
| `price-model-default.json` | the regression model (`{"YEAR\|TRIM": {a,b}}`) — **you create this** by copying from `scripts/value-model.example.json` and filling in coefficients for your target automobile's trims/years. The script reads it via `$HERMES_ARCHIVE_DIR/price-model-default.json`. |
| `visor_details_cpo_active.json` | listing_id → detail dict pulled from Visor.vin | Output of a scrape / the report pipeline. |
| `report_rows.json` | shortlisted rows (`{"picks": [...]}`) used for pick-flagging | Your selection step. |
| `automobile_rubric_scores.json` (output) | sorted scored leaderboard | Written here by this script. |

## How It Works

Six factors, each weighted:

1. **Value vs fair** (w .35): deviation from the regression-computed fair price.
2. **Wear regime** (w .20): actual miles vs expected odometer for that model year + age.
3. **Negotiation momentum** (w .15): days-on-market, price cuts, raised-price penalties.
4. **Warranty runway** (w .15): powertrain coverage ceiling minus current mileage.
5. **Model-year risk** (w .10): recall burden + do-not-drive-class recalls per MY.
6. **Liquidity** (w .10): $/mile-per-month retention proxy by trim.

> **Note:** the file is named `rubric-score.py` and reads inputs from `$HERMES_ARCHIVE_DIR`.
  Edit the three personalization blocks marked in the script; do not commit your real model
  data — it lives in `./archives/` which is gitignored.
