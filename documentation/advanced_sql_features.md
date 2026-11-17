# Advanced SQL Features

The SQL folder demonstrates MySQL warehouse and analytics patterns:

## Views

- vw_IFRS9_ECL
- vw_Portfolio_Health
- vw_DPD_Summary

## Indexes

- idx_loanid
- idx_poolid
- idx_borrowerid
- idx_region

## CTEs

- HighRiskLoans

## Window functions

- RANK()
- ROW_NUMBER()
- DENSE_RANK()
- Running portfolio balance
- Running ECL

## Stored procedures

- Refresh_Portfolio()

## Scope

These scripts are reusable MySQL examples for the optional warehouse path. The current Streamlit application reads CSV files directly so that the dashboard can run without a database connection.
