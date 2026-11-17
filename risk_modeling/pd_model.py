"""Reproducible baseline PD model for the synthetic loan portfolio.

The model deliberately uses origination-time features and excludes fields that
would leak current delinquency or loss outcomes. It is a portfolio-project
baseline, not a production or regulatory credit model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
NUMERIC_FEATURES = [
    "BorrowerAge",
    "AnnualIncome_INR",
    "CIBIL_Score_Origination",
    "DTI_Ratio",
    "LTV_AtOrigination",
    "OriginalLoanAmount",
    "OriginalTerm",
    "InterestRate",
    "MonthlyEMI",
]
CATEGORICAL_FEATURES = [
    "EmploymentType",
    "LoanPurpose",
    "OriginationChannel",
    "VehicleType",
    "Region",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def build_model() -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocess = ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocess),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    C=0.5,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def ks_statistic(y_true: np.ndarray, probability: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, probability)
    return float(np.max(tpr - fpr))


def run(data_path: Path, output_dir: Path) -> dict:
    df = pd.read_csv(data_path)
    y = pd.to_numeric(df["IsDefaulted"], errors="coerce").fillna(0).astype(int).to_numpy()
    X = df[FEATURES].copy()
    if np.unique(y).size != 2:
        raise ValueError("IsDefaulted must contain both non-default and default observations.")

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    oof_probability = np.zeros(len(df), dtype=float)
    fold_metrics = []
    for fold, (train_idx, test_idx) in enumerate(cv.split(X, y), start=1):
        model = build_model()
        model.fit(X.iloc[train_idx], y[train_idx])
        probability = model.predict_proba(X.iloc[test_idx])[:, 1]
        oof_probability[test_idx] = probability
        fold_metrics.append(
            {
                "fold": fold,
                "auc": round(float(roc_auc_score(y[test_idx], probability)), 4),
                "ks": round(ks_statistic(y[test_idx], probability), 4),
                "defaults_in_test": int(y[test_idx].sum()),
            }
        )

    metrics = {
        "model": "LogisticRegression",
        "target": "IsDefaulted",
        "rows": int(len(df)),
        "defaults": int(y.sum()),
        "default_rate": round(float(y.mean()), 4),
        "features": FEATURES,
        "evaluation": "3-fold stratified out-of-fold predictions",
        "random_state": RANDOM_STATE,
        "oof_auc": round(float(roc_auc_score(y, oof_probability)), 4),
        "oof_ks": round(ks_statistic(y, oof_probability), 4),
        "folds": fold_metrics,
    }

    final_model = build_model()
    final_model.fit(X, y)
    scored = df[["LoanID", "IsDefaulted"]].copy()
    scored["PD_Score_OOF"] = oof_probability.round(6)
    scored["PD_Score_Fitted"] = final_model.predict_proba(X)[:, 1].round(6)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "pd_model_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    scored.to_csv(output_dir / "pd_scores.csv", index=False)
    print(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate the baseline PD model.")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "auto_loan_securitisation_data.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "outputs" / "pd_model",
    )
    args = parser.parse_args()
    run(args.data, args.output_dir)


if __name__ == "__main__":
    main()
