from pathlib import Path

import pandas as pd
import pytest

from risk_modeling.ecl_engine import add_ecl_metrics, stress_ecl_table, weighted_ecl
from risk_modeling.pd_model import run


ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_portfolio_schema_and_uniqueness():
    loans = pd.read_csv(ROOT / "data" / "auto_loan_securitisation_data.csv")
    assert len(loans) == 500
    assert loans["LoanID"].is_unique
    assert {"IsDefaulted", "IFRS9_Stage", "PD_Estimate", "LGD_Estimate", "EAD"}.issubset(loans.columns)


def test_pd_model_generates_diagnostics(tmp_path):
    metrics = run(ROOT / "data" / "auto_loan_securitisation_data.csv", tmp_path)
    assert metrics["rows"] == 500
    assert metrics["defaults"] == 42
    assert 0 <= metrics["oof_auc"] <= 1
    assert 0 <= metrics["oof_ks"] <= 1
    assert 0 <= metrics["brier_score"] <= 1
    assert metrics["calibration_abs_error"] >= 0
    assert (tmp_path / "pd_model_metrics.json").exists()
    assert (tmp_path / "pd_scores.csv").exists()
    assert (tmp_path / "pd_feature_importance.csv").exists()


def test_ecl_engine_applies_dpd_staging_and_calculates_ecl():
    portfolio = pd.DataFrame(
        {
            "DelinquencyDays": [0, 30, 90],
            "DelinquencyStatus": ["Current", "30-59 DPD", "90-119 DPD"],
            "IsDefaulted": [False, False, False],
            "PD_Estimate": [0.10, 0.20, 0.30],
            "LGD_Estimate": [0.50, 0.50, 0.50],
            "EAD": [100.0, 100.0, 100.0],
        }
    )
    scored = add_ecl_metrics(portfolio)
    assert scored["Stage_Model"].tolist() == [1, 2, 3]
    assert scored["ECL_Model"].round(2).tolist() == [5.0, 20.0, 45.0]


def test_stress_engine_caps_values_and_weights_scenarios():
    portfolio = pd.DataFrame(
        {
            "DelinquencyDays": [90],
            "DelinquencyStatus": ["90-119 DPD"],
            "IsDefaulted": [False],
            "PD_Estimate": [0.80],
            "LGD_Estimate": [0.80],
            "EAD": [100.0],
        }
    )
    scored = add_ecl_metrics(portfolio)
    table = stress_ecl_table(scored, {"Base": (1.0, 1.0), "Severe": (2.0, 2.0)})
    assert table.loc[table["Scenario"] == "Severe", "Stress ECL"].iloc[0] == 300.0
    assert weighted_ecl(table, {"Base": 0.5, "Severe": 0.5}) == pytest.approx(246.0)
