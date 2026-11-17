from pathlib import Path

import pandas as pd

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
    assert metrics["oof_auc"] > 0.5
    assert 0 <= metrics["oof_ks"] <= 1
    assert (tmp_path / "pd_model_metrics.json").exists()
    assert (tmp_path / "pd_scores.csv").exists()
