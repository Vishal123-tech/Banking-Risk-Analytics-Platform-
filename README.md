# 🏦 Banking Risk Analytics Suite

> A reproducible portfolio project for a synthetic securitised auto-loan portfolio, combining a Streamlit dashboard, optional MySQL warehouse patterns, baseline PD modeling, IFRS 9-style risk analysis, and Power BI reporting.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/App-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![MySQL](https://img.shields.io/badge/SQL-MySQL-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![scikit--learn](https://img.shields.io/badge/Modeling-scikit--learn-F7931E?logo=scikit-learn&logoColor=111827)](https://scikit-learn.org/)
[![Power BI](https://img.shields.io/badge/Reporting-Power%20BI-F2C811?logo=powerbi&logoColor=111827)](https://powerbi.microsoft.com/)
[![CI tests](https://github.com/Vishal123-tech/Banking-Risk-Analytics-Platform-/actions/workflows/ci.yml/badge.svg)](https://github.com/Vishal123-tech/Banking-Risk-Analytics-Platform-/actions/workflows/ci.yml)

**Live demo:** [Open the Streamlit dashboard](https://n4dmtn9tondqgarhqhzkbn.streamlit.app/) · For local setup, see [RUN_INSTRUCTIONS.md](RUN_INSTRUCTIONS.md).

## Scope and data disclaimer

This is a synthetic, generic ABS-style auto-loan simulation. It uses Indian-style borrower fields such as INR and CIBIL scores alongside broadly used securitisation concepts such as servicers, repossession, waterfall cash flow, CPR, and stress scenarios. It is not a jurisdiction-specific RBI/Ind AS 109 implementation, a regulatory capital model, or a production credit decision system.

The checked-in sample contains 500 loans, 6,000 DPD snapshots, 12 monthly loss observations, and 375 vintage observations. The small sample is useful for demonstrating engineering and analytics patterns, but it is too small for production model validation.

## What is working today

- The Streamlit application reads the four checked-in CSV files directly and runs without a database connection.
- The MySQL folder is an optional warehouse implementation path with DDL, views, indexes, CTEs, window functions, and analytical queries.
- The baseline PD script uses origination-time features and 3-fold stratified out-of-fold evaluation.
- The Power BI report and screenshot gallery provide management-style reporting examples.

## Dashboard experience

| Dashboard | Decision support |
| --- | --- |
| Executive Summary | Portfolio balance, ECL, net loss, collection efficiency, and headline trends |
| Portfolio Overview | CIBIL, LTV, borrower, vehicle, and regional exposure |
| IFRS-9 | Stage exposure, provisions, and stage-level pricing indicators |
| DPD & Roll Rate | 30+/60+/90+ DPD exposure and prior-to-current delinquency transitions |
| Vintage | Cohort loss curves, pool factor, recoveries, and remaining balance |
| Dynamic Loss | Monthly gross loss, net loss, CPR, recoveries, and excess spread |
| Waterfall | Collections, recoveries, fees, principal, interest, and residual cash flows |
| Investor Reporting | Portfolio balance, 30+ DPD exposure, vintage losses, and cash-flow views |
| Stress Testing | Illustrative base, recession, COVID, and 2008 sensitivity scenarios |

Interactive filters cover reporting date, IFRS 9 stage, delinquency status, servicer, CIBIL score, and number format. The sidebar also includes filtered-loan CSV export and a data-quality snapshot.

## Screenshot gallery

Representative screenshots are stored in documentation/screenshots for browser-viewable previews:

| Streamlit DPD & Roll Rate | Power BI Executive Summary |
| --- | --- |
| ![Streamlit DPD and Roll Rate](documentation/screenshots/15-streamlit-dpd-roll-rate.png) | ![Power BI Executive Summary](documentation/screenshots/02-executive-summary.png) |

The supporting simulation screens have a clear three-step purpose:

1. **Scenario Arena:** choose the stress context.
2. **Scenario Brief:** review the mission, portfolio impact, and available analyses.
3. **Decision Centre:** choose a risk-management response and review the recommended analysis path.

The PBIX report requires Power BI Desktop; the screenshots provide a lightweight preview for GitHub visitors.

For a printable preview, open powerbi/Securitisation_Risk_Analytics_screenshot_preview.pdf.

## Key findings from the checked-in sample

- Stage 1 represents 44.61% of current balance; Stage 2 represents 31.94%; Stage 3 represents 23.45%. Stage 2 plus Stage 3 therefore accounts for 55.39% of current balance.
- The largest direct worsening transition in the DPD matrix is Current → 1–29 DPD at 10.00%; the 30–59 DPD → 60–89 DPD transition is 8.25%.
- Base ECL is ₹16.43M. With the capped stress calculation, Severe Recession ECL rises to ₹32.04M, a 95% increase; illustrative 2008 Crisis ECL rises to ₹49.29M, or 3.0× base ECL.
- The regenerated sample contains 42 default events out of 500 loans, an observed default rate of 8.4%.

## Baseline PD model

The repository includes risk_modeling/pd_model.py, a reproducible logistic-regression baseline for default classification.

### Engineering choices

- Uses origination-time information such as origination CIBIL score, income, DTI, LTV, loan amount, term, rate, borrower profile, vehicle type, channel, and region.
- Excludes current delinquency, loss, ECL, and default-outcome fields from the feature set to reduce target leakage.
- Handles missing values, scales numeric features, one-hot encodes categorical features, and applies class-balanced logistic regression.
- Uses a fixed random seed of 42 and 3-fold stratified out-of-fold predictions.

### Sample diagnostics

| Metric | Result |
| --- | ---: |
| Rows | 500 |
| Default events | 42 |
| Out-of-fold AUC | 0.7252 |
| Out-of-fold KS | 0.3903 |

The synthetic generator derives the default label from CIBIL, DTI, LTV, and a random noise term by construction, so this result demonstrates recovery of a known simulated signal rather than production predictive power. The sample is still small and synthetic; the AUC is a reproducible modeling diagnostic, not a validated credit scorecard.

Run it with:

```bash
python risk_modeling/pd_model.py
```

The script writes metrics and loan-level PD scores to outputs/pd_model.

## Simplified IFRS 9 and stress assumptions

The dashboard uses supplied synthetic PD_Estimate, LGD_Estimate, EAD, and ECL_Provision fields. The stress-testing page applies:

```text
Stress ECL = Base ECL × capped PD factor × capped LGD factor
```

This is intentionally simplified. It does not implement:

- 12-month ECL for Stage 1 versus lifetime ECL for Stages 2 and 3.
- Discounting of expected cash shortfalls at the effective interest rate.
- Probability-weighted forward-looking macroeconomic scenarios.
- Calibrated transition matrices, PIT/TTC PDs, or regulatory capital treatment.

The scenario multipliers are illustrative sensitivity assumptions, not calibrated values:

The application caps stressed PD and LGD at 1.0 before calculating ECL, so a multiplier cannot create an impossible probability or loss-given-default above 100%.

| Scenario | PD multiplier | LGD multiplier |
| --- | ---: | ---: |
| Base | 1.00× | 1.00× |
| Mild Recession | 1.25× | 1.10× |
| Severe Recession | 1.50× | 1.30× |
| COVID Shock | 1.80× | 1.20× |
| 2008 Crisis | 2.00× | 1.50× |

## Architecture and data flow

```mermaid
flowchart LR
    A[Four CSV source tables] --> B[Python loading and validation]
    B --> C[Current Streamlit CSV demo]
    A -. optional load .-> D[MySQL warehouse tables]
    D --> E[MySQL views and analytics SQL]
    E -. optional reporting .-> F[SQL outputs]
    B --> G[Baseline PD model]
    G --> H[PD diagnostics and scores]
    A -. direct import .-> I[Power BI report / PDF preview]
```

The solid path is the currently working Streamlit demo. The dotted path is the optional MySQL implementation route; the current Streamlit app does not yet query MySQL directly.

## Reproducibility

Generate a fresh synthetic portfolio without overwriting the checked-in sample:

```bash
python data/generate_synthetic_portfolio.py --seed 42 --output-dir data/generated
```

The generator creates 500 loans, 6,000 snapshots, 12 monthly loss rows, and 375 vintage rows by default. The fixed seed makes the generated sample repeatable.

## SQL scope

This project uses MySQL as its database target. The SQL layer is documented honestly as an optional warehouse-pattern implementation:

- create_tables.sql — warehouse table definitions.
- indexes.sql — query-performance indexes.
- views.sql — reusable portfolio and IFRS 9 views.
- ctes.sql — high-risk loan analysis with CTEs.
- window_functions.sql — rankings and running metrics.
- stored_procedures.sql — refresh procedure example.
- banking_analytics.sql — portfolio-level queries.
- ifrs9_analytics.sql — ECL and stage analysis.
- roll_rate_analytics.sql — DPD transition analysis.
- vintage_analytics.sql — cohort performance.
- collection_analytics.sql — collections and recoveries.
- stress_testing_framework.sql — scenario sensitivity analysis.

## Data-quality approach

The application and tests cover:

- Required file availability and schema checks.
- Date parsing and standardized reporting dates.
- Duplicate LoanID detection.
- Missing-value snapshots.
- Filter-aware portfolio calculations.
- Leakage-aware PD feature selection.
- Reproducible synthetic-data generation.

## Reproduce and test locally

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements-dev.txt
python -m streamlit run app.py
pytest -q
```

The repository also includes a GitHub Actions workflow that compiles the Python files and runs pytest on pushes and pull requests.

## Repository structure

```text
Banking-Risk-Analytics-Platform-/
├── app.py
├── data/
│   ├── auto_loan_securitisation_data.csv
│   ├── dpd_snapshot_history.csv
│   ├── dynamic_loss_monthly.csv
│   ├── static_pool_vintage_data.csv
│   └── generate_synthetic_portfolio.py
├── risk_modeling/
│   └── pd_model.py
├── etl/                              # Extract, load, validation, and connection utilities
├── sql/                              # Optional MySQL warehouse and analytics scripts
├── documentation/
│   ├── data_dictionary.md
│   ├── warehouse_architecture.md
│   ├── advanced_sql_features.md
│   ├── stress_testing_framework.md
│   └── screenshots/
├── powerbi/
│   ├── Securitisation_Risk_Analytics.pbix
│   ├── Securitisation_Risk_Analytics_screenshot_preview.pdf
│   └── README.md
├── tests/
├── .github/workflows/ci.yml
├── requirements.txt
├── requirements-dev.txt
├── RUN_INSTRUCTIONS.md
└── LICENSE
```

## Business impact

The project supports risk and operations teams by helping them:

- Prioritize collection review using DPD transitions and high-risk exposures.
- Identify provisioning pressure under illustrative stress scenarios.
- Compare portfolio quality across IFRS 9 stages, servicers, regions, and vintages.
- Review cash-flow waterfall performance and investor-facing portfolio trends.
- Move from descriptive reporting toward reproducible, testable risk analytics.

## Limitations and next steps

- Replace synthetic fields with observed loan-level performance and macroeconomic history.
- Build a larger default sample and recalibrate the PD model before interpreting AUC/KS.
- Connect the Streamlit app to a MySQL view or a production-style warehouse layer.
- Add proper lifetime ECL, effective-interest discounting, and probability-weighted scenarios.
- Align the policy framing to a selected jurisdiction, such as RBI/Ind AS 109, if the project is presented as India-specific.
- Add a native Power BI PDF export after opening the PBIX in Power BI Desktop.

## License

MIT License. The data in this repository is synthetic and generated by `data/generate_synthetic_portfolio.py`.

## Author

**Vishal Yadav**

[GitHub profile](https://github.com/Vishal123-tech) · [Project repository](https://github.com/Vishal123-tech/Banking-Risk-Analytics-Platform-)
