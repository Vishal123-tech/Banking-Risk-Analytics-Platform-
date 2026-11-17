"""Transparent portfolio ECL calculations for the synthetic risk demo.

This module intentionally implements a simplified, auditable ECL engine rather
than presenting the supplied ECL field as a calculated result.  The staging
rules are DPD-based: 30+ DPD maps to Stage 2 and 90+ DPD maps to Stage 3.
Stage 1 uses a 12-month PD proxy; Stage 2 and Stage 3 apply illustrative
lifetime-horizon multipliers of 2.0x and 3.0x respectively.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

STAGE_LABELS = {1: "Stage 1", 2: "Stage 2", 3: "Stage 3"}
LIFETIME_MULTIPLIERS = {1: 1.0, 2: 2.0, 3: 3.0}


def derive_stage(dpd: pd.Series) -> pd.Series:
    """Apply the simplified DPD staging policy to a delinquency series."""

    days = pd.to_numeric(dpd, errors="coerce").fillna(0)
    return pd.Series(
        np.select([days >= 90, days >= 30], [3, 2], default=1),
        index=dpd.index,
        dtype="int64",
    )


def add_ecl_metrics(
    portfolio: pd.DataFrame,
    *,
    pd_column: str = "PD_Estimate",
    lgd_column: str = "LGD_Estimate",
    ead_column: str = "EAD",
) -> pd.DataFrame:
    """Return a copy with transparent stage, PD, LGD, and ECL calculations."""

    out = portfolio.copy()
    stage = derive_stage(out["DelinquencyDays"])
    hard_default = out["DelinquencyStatus"].isin(["Default", "Repossessed"])
    if "IsDefaulted" in out:
        hard_default = hard_default | out["IsDefaulted"].fillna(False).astype(bool)
    stage = stage.mask(hard_default, 3)

    pd_12m = pd.to_numeric(out[pd_column], errors="coerce").fillna(0).clip(0, 1)
    pd_12m = pd_12m.mask(hard_default, 1.0)
    lgd = pd.to_numeric(out[lgd_column], errors="coerce").fillna(0).clip(0, 1)
    ead = pd.to_numeric(out[ead_column], errors="coerce").fillna(0).clip(lower=0)
    lifetime_multiplier = stage.map(LIFETIME_MULTIPLIERS).astype(float)

    out["Stage_Model"] = stage
    out["Stage_Model_Label"] = stage.map(STAGE_LABELS)
    out["PD_12M_Model"] = pd_12m
    out["LGD_Model"] = lgd
    out["Lifetime_Multiplier"] = lifetime_multiplier
    out["ECL_Model"] = pd_12m * lgd * ead * lifetime_multiplier
    return out


def stress_ecl_table(
    portfolio: pd.DataFrame,
    scenarios: Mapping[str, tuple[float, float]],
) -> pd.DataFrame:
    """Calculate capped per-loan stress ECL for each scenario."""

    base_ecl = float(portfolio["ECL_Model"].sum())
    rows: list[dict[str, float | str]] = []
    for name, (pd_multiplier, lgd_multiplier) in scenarios.items():
        stressed_pd = (portfolio["PD_12M_Model"] * pd_multiplier).clip(upper=1.0)
        stressed_lgd = (portfolio["LGD_Model"] * lgd_multiplier).clip(upper=1.0)
        stress_ecl = float((stressed_pd * stressed_lgd * portfolio["EAD"] * portfolio["Lifetime_Multiplier"]).sum())
        rows.append(
            {
                "Scenario": name,
                "Base ECL": base_ecl,
                "Stress ECL": stress_ecl,
                "ECL Increase": stress_ecl - base_ecl,
                "ECL Increase %": (stress_ecl / base_ecl - 1) if base_ecl else 0.0,
                "Stress PD": float(stressed_pd.mean()),
                "Stress LGD": float(stressed_lgd.mean()),
                "PD Multiplier Applied": pd_multiplier,
                "LGD Multiplier Applied": lgd_multiplier,
            }
        )
    return pd.DataFrame(rows)


def weighted_ecl(stress_table: pd.DataFrame, weights: Mapping[str, float]) -> float:
    """Return probability-weighted stress ECL, normalising selected weights."""

    selected = stress_table[stress_table["Scenario"].isin(weights)].copy()
    selected["Weight"] = selected["Scenario"].map(weights).astype(float)
    total_weight = float(selected["Weight"].sum())
    if total_weight <= 0:
        return float(selected["Stress ECL"].mean()) if len(selected) else 0.0
    return float((selected["Stress ECL"] * selected["Weight"]).sum() / total_weight)
