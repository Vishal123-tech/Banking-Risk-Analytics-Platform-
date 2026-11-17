"""Generate a reproducible synthetic portfolio for the dashboard.

The default output is data/generated so the checked-in sample is never
overwritten accidentally. Use --seed to reproduce the same sample exactly.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
DPD_BUCKETS = ["Current", "1-29 DPD", "30-59 DPD", "60-89 DPD", "90-119 DPD", "120+ DPD", "Default", "Repossessed"]
STATES = ["Maharashtra", "Karnataka", "Delhi", "Gujarat", "Tamil Nadu", "Rajasthan", "West Bengal"]
REGIONS = ["West", "South", "North", "Central", "East"]
SERVICERS = ["Bajaj Finance Auto", "HDFC Bank Auto Finance", "ICICI Auto Loans"]
VEHICLE_TYPES = ["Hatchback", "Sedan", "SUV", "MUV", "Compact SUV"]


def generate_loans(rng: np.random.Generator, n: int) -> pd.DataFrame:
    loan_id = np.array([f"L{idx:05d}" for idx in range(1, n + 1)])
    origination = pd.Timestamp("2022-01-01") + pd.to_timedelta(rng.integers(0, 730, n), unit="D")
    original_amount = rng.lognormal(mean=np.log(1_050_000), sigma=0.45, size=n).round(2)
    original_term = rng.choice([24, 36, 48, 60], n)
    months_on_book = rng.integers(2, original_term, n)
    remaining_term = np.maximum(original_term - months_on_book, 1)
    cibil_orig = np.clip(rng.normal(730, 55, n), 520, 880).round().astype(int)
    cibil_current = np.clip(cibil_orig + rng.normal(3, 22, n), 500, 900).round().astype(int)
    income = rng.lognormal(mean=np.log(1_200_000), sigma=0.5, size=n).round(2)
    dti = np.clip(rng.normal(0.34, 0.12, n), 0.08, 0.85).round(4)
    ltv_orig = np.clip(rng.normal(0.72, 0.14, n), 0.35, 1.05).round(4)
    pd_est = np.clip(0.01 + (700 - cibil_orig) * 0.00035 + (dti - 0.3) * 0.06 + (ltv_orig - 0.7) * 0.04, 0.005, 0.35)
    is_defaulted = rng.random(n) < pd_est
    current_balance = (original_amount * rng.uniform(0.45, 0.98, n)).round(2)
    current_vehicle_value = (original_amount / ltv_orig * rng.uniform(0.65, 1.0, n)).round(2)
    status_prob = np.clip(pd_est * 2.5, 0.01, 0.35)
    delinquency_status = np.array([
        rng.choice(DPD_BUCKETS, p=[1 - p, p * 0.25, p * 0.18, p * 0.14, p * 0.10, p * 0.08, p * 0.18, p * 0.07])
        for p in status_prob
    ])
    delinquency_days = pd.Series(delinquency_status).map({
        "Current": 0, "1-29 DPD": 15, "30-59 DPD": 45, "60-89 DPD": 75,
        "90-119 DPD": 105, "120+ DPD": 140, "Default": 180, "Repossessed": 210,
    }).to_numpy()
    stage = np.select([pd_est >= 0.12, pd_est >= 0.045], [3, 2], default=1).astype(int)
    lgd = rng.uniform(0.25, 0.70, n).round(4)
    ead = (current_balance * rng.uniform(0.90, 1.05, n)).round(2)
    ecl = (pd_est * lgd * ead).round(2)
    original_vehicle_value = (original_amount / ltv_orig).round(2)
    last_payment = (current_balance / np.maximum(remaining_term, 1) * rng.uniform(0.85, 1.15, n)).round(2)
    vehicle_make = rng.choice(["Maruti", "Hyundai", "Tata", "Mahindra", "Honda"], n)
    vehicle_model = np.array([f"{make}-{idx % 5 + 1}" for idx, make in enumerate(vehicle_make)])
    return pd.DataFrame({
        "AnnualIncome_INR": income, "BorrowerAge": rng.integers(22, 66, n),
        "BorrowerID": [f"B{idx:05d}" for idx in range(1, n + 1)],
        "CIBIL_Score_Current": cibil_current, "CIBIL_Score_Origination": cibil_orig,
        "CurrentBalance": current_balance, "CurrentVehicleValue": current_vehicle_value,
        "CutoffDate": pd.Timestamp("2024-10-30"), "DelinquencyDays": delinquency_days,
        "DelinquencyStatus": delinquency_status, "DTI_Ratio": dti, "EAD": ead,
        "ECL_Provision": ecl, "EmploymentType": rng.choice(["Salaried", "Self-employed", "Business"], n),
        "HasInsurance": rng.choice([True, False], n, p=[0.78, 0.22]),
        "IFRS9_Stage": stage, "InsuranceType": rng.choice(["Comprehensive", "Third Party", "None"], n),
        "InterestRate": rng.uniform(8.5, 15.5, n).round(4), "IsDefaulted": is_defaulted,
        "IsModified": rng.choice([True, False], n, p=[0.08, 0.92]),
        "IsNewVehicle": rng.choice([True, False], n, p=[0.62, 0.38]),
        "LastPaymentAmount": last_payment, "LastPaymentDate": origination + pd.to_timedelta(months_on_book * 30, unit="D"),
        "LGD_Estimate": lgd, "LoanID": loan_id, "LoanPurpose": rng.choice(["Auto Purchase", "Refinance"], n),
        "LossAmount": (ecl * rng.uniform(0.8, 1.3, n)).round(2), "LTV_AtOrigination": ltv_orig,
        "LTV_Current": np.clip(ltv_orig * rng.uniform(0.75, 1.15, n), 0.25, 1.20).round(4),
        "MaturityDate": origination + pd.to_timedelta(original_term * 30, unit="D"),
        "OriginationDate": origination, "ModificationType": rng.choice(["None", "Tenure Extension", "Rate Reduction"], n),
        "MonthlyEMI": (original_amount / original_term * rng.uniform(1.05, 1.35, n)).round(2),
        "MonthsOnBook": months_on_book, "NetLoss": (ecl * rng.uniform(0.5, 1.2, n)).round(2),
        "OriginalLoanAmount": original_amount, "OriginalTerm": original_term,
        "OriginalVehicleValue": original_vehicle_value, "OriginationChannel": rng.choice(["Dealer", "Digital", "Branch"], n),
        "PD_Estimate": pd_est.round(6), "PoolID": rng.choice(["Pool-A", "Pool-B", "Pool-C"], n),
        "PrepaymentAmount": (current_balance * rng.uniform(0, 0.03, n)).round(2),
        "RecoveryAmount": (ecl * rng.uniform(0.1, 0.6, n)).round(2), "Region": rng.choice(REGIONS, n),
        "RemainingTerm": remaining_term, "ScheduledPaymentDue": last_payment,
        "ServicerID": rng.choice(["S001", "S002", "S003"], n), "ServicerName": rng.choice(SERVICERS, n),
        "State": rng.choice(STATES, n), "Times30DPD_Last12M": rng.integers(0, 5, n),
        "Times60DPD_Last12M": rng.integers(0, 4, n), "Times90DPD_Last12M": rng.integers(0, 3, n),
        "TotalPaymentsDue": months_on_book, "TotalPaymentsMade": np.maximum(months_on_book - rng.integers(0, 3, n), 0),
        "VehicleMake": vehicle_make, "VehicleModel": vehicle_model, "VehicleType": rng.choice(VEHICLE_TYPES, n),
        "VehicleYear": rng.integers(2016, 2025, n),
    })


def generate_snapshots(rng: np.random.Generator, loans: pd.DataFrame) -> pd.DataFrame:
    dates = pd.date_range("2024-01-30", periods=12, freq="ME")
    n = len(loans)
    current = rng.choice(DPD_BUCKETS, size=n * len(dates), p=[0.55, 0.10, 0.08, 0.07, 0.06, 0.05, 0.06, 0.03])
    prior = rng.choice(DPD_BUCKETS, size=n * len(dates), p=[0.58, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.02])
    days = pd.Series(current).map({
        "Current": 0, "1-29 DPD": 15, "30-59 DPD": 45, "60-89 DPD": 75,
        "90-119 DPD": 105, "120+ DPD": 140, "Default": 180, "Repossessed": 210,
    }).to_numpy()
    loan_values = np.tile(loans["CurrentBalance"].to_numpy(), len(dates))
    transition = np.where(current == prior, "Stable", np.where(days > 0, "Roll Forward", "Cure"))
    return pd.DataFrame({
        "AmountOverdue": (loan_values * rng.uniform(0, 0.08, len(current))).round(2),
        "ConsecutiveMonthsDelinquent": rng.integers(0, 7, len(current)),
        "CureFlag": transition == "Cure", "CurrentBalance": loan_values,
        "DPD_Bucket": current, "DPD_Bucket_Prior": prior, "DPD_Days": days,
        "EMIsOverdue": rng.integers(0, 7, len(current)),
        "LastPaymentAmount": np.tile(loans["LastPaymentAmount"].to_numpy(), len(dates)),
        "LastPaymentDate": np.tile(loans["LastPaymentDate"].to_numpy(), len(dates)),
        "LoanID": np.tile(loans["LoanID"].to_numpy(), len(dates)),
        "PoolID": np.tile(loans["PoolID"].to_numpy(), len(dates)),
        "RBI_SMA_Class": rng.choice(["Standard", "SMA-0", "SMA-1", "NPA"], len(current)),
        "RepossessionFlag": current == "Repossessed", "RollFlag": transition == "Roll Forward",
        "SnapshotDate": np.repeat(dates, n), "TransitionType": transition,
        "WriteOffFlag": current == "Default",
    })


def generate_monthly_loss(rng: np.random.Generator, loans: pd.DataFrame) -> pd.DataFrame:
    dates = pd.date_range("2023-12-30", periods=12, freq="ME")
    bop = float(loans["CurrentBalance"].sum())
    rows = []
    for idx, date in enumerate(dates):
        collections = bop * rng.uniform(0.045, 0.085)
        recoveries = bop * rng.uniform(0.006, 0.018)
        gross_loss = bop * rng.uniform(0.002, 0.009)
        scheduled = bop * rng.uniform(0.012, 0.025)
        prepayments = bop * rng.uniform(0.002, 0.012)
        net_loss = max(gross_loss - recoveries, 0)
        rows.append({
            "BillingAmount": collections + scheduled, "BOP_Balance": bop, "BOP_LoanCount": len(loans),
            "CollectionEfficiency": collections / max(collections + scheduled, 1), "CollectionsTotal": collections,
            "CPR_Annualised": rng.uniform(0.04, 0.24), "EOP_Balance": bop - scheduled - prepayments,
            "EOP_LoanCount": len(loans) - idx, "ExcessSpread_Monthly": collections - net_loss,
            "GrossLoss_ThisMonth": gross_loss, "MonthlyDefaultRate": rng.uniform(0.001, 0.008),
            "MonthlyNetLossRate": net_loss / max(bop, 1), "NetLoss_ThisMonth": net_loss,
            "NewDefaults_Balance": gross_loss, "NewDefaults_Count": int(rng.integers(1, 12)),
            "Prepayments_ThisMonth": prepayments, "Recoveries_ThisMonth": recoveries,
            "ReportingDate": date, "ScheduledAmort": scheduled, "SMM": prepayments / max(bop, 1),
        })
        bop = rows[-1]["EOP_Balance"]
    return pd.DataFrame(rows)


def generate_vintage(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for vintage_idx in range(1, 16):
        start = pd.Timestamp("2021-01-01") + pd.DateOffset(months=(vintage_idx - 1) * 3)
        original = float(rng.uniform(15_000_000, 45_000_000))
        for mob in range(25):
            gross = original * rng.uniform(0.001, 0.004) * (mob + 1)
            recoveries = gross * rng.uniform(0.10, 0.45)
            rows.append({
                "CumulativeDefaults_Balance": gross, "CumulativeDefaults_Count": int(gross / 500_000),
                "CumulativeGrossLoss": gross, "CumulativeNetLoss": gross - recoveries,
                "CumulativeNetLossRate": (gross - recoveries) / original,
                "CumulativePrepayments": original * rng.uniform(0.001, 0.008) * (mob + 1),
                "CumulativeRecoveries": recoveries, "CurrentDelinq30Plus": int(rng.integers(0, 25)),
                "MarginalLossRate": rng.uniform(0.001, 0.01), "MonthsOnBook": mob,
                "OriginalLoanCount": int(rng.integers(100, 450)), "OriginalPoolBalance": original,
                "PoolFactor": max(1 - mob * 0.025, 0.05), "RemainingPoolBalance": original * max(1 - mob * 0.025, 0.05),
                "VintageID": f"V{vintage_idx:02d}", "VintageStartDate": start,
            })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reproducible synthetic portfolio CSVs.")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "generated")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--loans", type=int, default=500)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    loans = generate_loans(rng, args.loans)
    snapshots = generate_snapshots(rng, loans)
    monthly_loss = generate_monthly_loss(rng, loans)
    vintage = generate_vintage(rng)
    loans.to_csv(output / "auto_loan_securitisation_data.csv", index=False)
    snapshots.to_csv(output / "dpd_snapshot_history.csv", index=False)
    monthly_loss.to_csv(output / "dynamic_loss_monthly.csv", index=False)
    vintage.to_csv(output / "static_pool_vintage_data.csv", index=False)
    print(f"Generated {len(loans):,} loans, {len(snapshots):,} snapshots, {len(monthly_loss):,} loss rows, and {len(vintage):,} vintage rows in {output}.")


if __name__ == "__main__":
    main()
