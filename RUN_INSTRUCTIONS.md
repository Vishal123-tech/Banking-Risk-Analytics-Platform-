# Banking Risk Analytics Suite — Run Guide

## Local Streamlit dashboard

The dashboard reads the four checked-in CSV files from data/ and does not require MySQL for the interactive demo.

### Windows PowerShell

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements-dev.txt
python -m streamlit run app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m streamlit run app.py
```

Open the local URL shown by Streamlit, normally http://localhost:8501.

## Reproducible synthetic data

The checked-in sample is preserved. Generate a fresh deterministic sample into a separate folder:

```bash
python data/generate_synthetic_portfolio.py --seed 42 --output-dir data/generated
```

## Baseline PD model

Run the leakage-aware logistic-regression baseline:

```bash
python risk_modeling/pd_model.py
```

The command writes AUC/KS diagnostics and loan-level scores to outputs/pd_model.

## Tests

```bash
pytest -q
```

GitHub Actions runs compilation and pytest on pushes and pull requests.

## Optional MySQL workflow

The Streamlit app currently reads CSV files directly. The SQL folder is an optional MySQL warehouse path:

1. Review documentation/warehouse_architecture.md and documentation/data_dictionary.md.
2. Create tables with sql/create_tables.sql.
3. Apply sql/indexes.sql and sql/views.sql.
4. Run the analytical scripts for IFRS 9, roll rates, vintage, collections, and stress testing.
5. Connect the resulting MySQL views to a BI tool if required.

## Power BI

Open powerbi/Securitisation_Risk_Analytics.pbix in Power BI Desktop. The repository also contains screenshot previews because PBIX files require Power BI Desktop.

## Troubleshooting

- **Data files not found:** run Streamlit from the repository root and confirm the four CSV files are inside data/.
- **PowerShell blocks activation:** run Set-ExecutionPolicy -Scope Process Bypass for the current terminal, then activate .venv again.
- **Port already in use:** run python -m streamlit run app.py --server.port 8502.
- **SQL connection errors:** the interactive demo is CSV-based; MySQL is only required for the optional warehouse workflow.
