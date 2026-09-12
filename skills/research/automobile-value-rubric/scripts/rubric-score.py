# Rubric scorer v2 — parses nested vehicle/pricing reprs from cached API detail pulls.
# Generic fork of an internal Bronco-only pipeline (Sep 2026).
# stdlib only. All input/output files live under $HERMES_ARCHIVE_DIR (default ./archives).

import json, ast, os
from pathlib import Path

# ── Resolve archive directory ────────────────────────────────────────────────
ARCH = os.environ.get("HERMES_ARCHIVE_DIR", str(Path(__file__).resolve().parents[3] / "archives"))

model_file   = f"{ARCH}/price-model-default.json"          # {YEAR|TRIM: {a, b}}  — YOU CREATE THIS (copy from value-model.example.json)
active_file  = f"{ARCH}/visor_details_cpo_active.json"    # listing_id -> detail dict  — Visor.vin scrape output
picks_file   = f"{ARCH}/report_rows.json"                  # {"picks": [...]}        — your shortlisted rows
out_file      = f"{ARCH}/automobile_rubric_scores.json"   # scored leaderboard (output)

# ── Personalization: regression model ───────────────────────────────────────
# Copy value-model.example.json → price-model-default.json and fill it for YOUR vehicle.
model  = json.load(open(model_file)) if os.path.exists(model_file) else {}
active = json.load(open(active_file))   if os.path.exists(active_file)  else {}
picks  = {p["vin"] for p in json.load(open(picks_file)).get("picks", [])} if os.path.exists(picks_file) else set()

flag_suspicious_cert = set()  # VINs sold-day-then-relisted-certified (populate from history audit)

def parse(v):
    if isinstance(v, str) and v.startswith("{"): return ast.literal_eval(v)
    return v

def fair(year, trim, miles):
    alias = {}   # >>> PERSONALIZE <<< : map package trims to base-trim cohort, e.g. {"Limited Plus": "Limited"}
    t2 = alias.get(trim)
    k = f"{year}|{trim}" if f"{year}|{trim}" in model else (f"{year}|{t2}" if (t2 and f"{year}|{t2}" in model) else None)
    m = model.get(k) if k else None
    if not m: return None
    prem = 1.0   # sold cohorts already include package examples — NEVER double-count premium
    return max(1200, (m["a"] + m["b"] * miles) * prem)

# ── Personalization: model-year recall burden & do-not-drive class ───────────
# >>> PERSONALIZE <<< : replace these example tables with values for YOUR automobile.
RECALLS = {2021: 4, 2022: 6, 2023: 5, 2024: 3, 2025: 2}   # NHTSA recall count per MY (web-sourced)
DND      = {}                                            # MYs with active do-not-drive-class recalls

# ── Personalization: expected odometer by model year ────────────────────────
# >>> PERSONALIZE <<< : adjust for your vehicle's market segment.
exp_mi_table = {2023: 18_000, 2024: 12_000, 2025: 6_000}

def score(r):
    veh   = parse(r.get("vehicle") or {})
    build = veh.get("build") or {}
    year, trim = build.get("year"), build.get("trim")
    miles  = int(parse(r.get("miles")) if not isinstance(r.get("miles"), int) else r["miles"])
    price  = int(r["price"]) if str(r.get("price", "")).isdigit() else None
    dom    = r.get("days_on_market", 0) or 0
    ph     = sorted(r.get("price_history") or [], key=lambda x: x["changed_at"])

    # 1) value vs fair (w .35): +6% over -> 0 ... -8% under -> 5 linear
    f = fair(year, trim, miles) if year and price is not None else None
    dev = None if not f else (price - f) / f
    v_val = 3.0 if dev is None else max(0.0, min(5.0, round(5 * (0.06 - dev) / 0.14, 2)))

    # 2) wear regime (w .20): expected odometer by snapshot date per MY
    exp_mi = exp_mi_table.get(year, 15_000) if year else 15_000
    ratio  = miles / exp_mi
    s_wear = max(0.5, min(5, 5 - max(0, (ratio - 1) * 2.5)))
    if miles <= 8_000: s_wear = min(5, s_wear + .5)
    if miles >= 60_000: s_wear = max(1, s_wear - .5)

    # 3) negotiation momentum (w .15): DOM + cuts; raised price penalized
    ever_cut = len(ph) >= 2 and ph[0]["price_after"] > ph[-1]["price_after"]
    raised   = len(ph) >= 2 and ph[0]["price_after"] < ph[-1]["price_after"]
    s_mot = 3.0
    if dom >= 90:  s_mot += .75
    elif dom <= 14: s_mot -= .75
    if ever_cut:   s_mot += .75
    if raised:     s_mot -= 1.5
    s_mot = max(0, min(5, round(s_mot, 2)))

    # 4) warranty runway (w .15): powertrain ceiling (configurable per vehicle class)
    # >>> PERSONALIZE <<< : set the right mileage cap for your target automobile.
    WARRANTY_CAP_MILES = 100_000   # standard powertrain; adjust if your model differs
    rem_mi = max(0, WARRANTY_CAP_MILES - miles)
    s_cov = min(5, round(1 + (rem_mi / WARRANTY_CAP_MILES) * 4, 2))
    if r["vin"] in flag_suspicious_cert: s_cov = max(1, s_cov - 1.5)

    # 5) model-year risk (w .10): recall burden + do-not-drive class
    rc = RECALLS.get(year, 3) if year else 3   # fallback assumes moderate recall count
    s_risk = round(max(1, min(5, 5 - rc / 6 - DND.get(year, 0) * .8)), 2)

    # 6) liquidity (w .10): $/mile-per-month retention proxy by trim
    # >>> PERSONALIZE <<< : replace with trims + liquidity scores for YOUR vehicle.
    ppm_by_trim = {   # example mid-size SUV values
        "TRD Pro": 2.0, "Limited": 1.6, "XSE": 1.5, "LE": 1.3, "Base": 1.2,
    }
    s_liq = min(5, round(2 + ppm_by_trim.get(trim, 1), 2))

    total = round(v_val * .35 + s_wear * .20 + s_mot * .15 + s_cov * .15 + s_risk * .10 + s_liq * .10, 2)
    dealer  = parse(r.get("dealer") or {})
    pricing = parse(r.get("pricing") or {})

    return dict(
        vin=r["vin"], id=r["id"], year=year, trim=trim, miles=miles, price=price, dom=dom,
        dealer_name=dealer.get("name"), city=dealer.get("city"), state=dealer.get("state"),
        otd=pricing.get("seller_total_before_taxes_and_registration_usd"),
        fair=None if not f else round(f, -1), dev=None if dev is None else round(dev * 100, 1),
        cuts=max(0, len(ph) - 1), ever_cut=bool(ever_cut), raised=bool(raised), pick=r["vin"] in picks,
        score=total)

rows = [score(d) for _, d in active.items() if d]
rows.sort(key=lambda x: -x["score"])
json.dump(rows, open(out_file, "w"), indent=1)
print(f"{len(rows)} scored / {len(active)} pulled")
assert len(set(r['score'] for r in rows)) > 3, "scores do not discriminate"
