# Banking Risk Analytics Platform — Run Guide

## Local Streamlit app

The dashboard reads the four CSV files from data/ and does not require MySQL for the interactive demo.

### Repository layout

```text
app.py
requirements.txt
.streamlit/config.toml
data/
  auto_loan_securitisation_data.csv
  dpd_snapshot_history.csv
  dynamic_loss_monthly.csv
  static_pool_vintage_data.csv
```

### Windows PowerShell

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

1. Push the repository to GitHub and keep app.py and data/ at the repository root.
2. Open share.streamlit.io and create an app from the repository.
3. Select app.py as the main file.
4. Every git push can trigger a fresh deployment.

## Optional SQL / Power BI workflow

1. Review documentation/warehouse_architecture.txt and documentation/data_dictionary.txt.
2. Create tables using sql/create_tables.sql.
3. Apply sql/indexes.sql, sql/views.sql, and the analytical SQL files as needed.
4. Use the utilities in etl/ for validation and loading experiments.
5. Open powerbi/Securitisation_Risk_Analytics.pbix in Power BI Desktop for the report layer.

## Troubleshooting

- **Data files not found:** run Streamlit from the repository root and confirm the four CSV files are inside data/.
- **PowerShell blocks activation:** run Set-ExecutionPolicy -Scope Process Bypass for the current terminal, then activate .venv again.
- **Port already in use:** run streamlit run app.py --server.port 8502.
- **SQL connection errors:** the Streamlit demo reads CSVs directly; database connectivity is only needed for the optional ETL workflow.
