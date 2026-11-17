# Data Dictionary

## DimBorrower

| Field | Meaning |
| --- | --- |
| BorrowerID | Synthetic borrower identifier |
| BorrowerAge | Borrower age |
| EmploymentType | Employment category |
| AnnualIncome_INR | Annual income in INR |
| DTI_Ratio | Debt-to-income ratio |
| CIBIL_Score_Origination | Credit score at origination |
| CIBIL_Score_Current | Current credit score |

## DimVehicle

| Field | Meaning |
| --- | --- |
| VehicleMake | Vehicle manufacturer |
| VehicleModel | Vehicle model |
| VehicleYear | Vehicle model year |
| VehicleType | Vehicle category |
| OriginalVehicleValue | Vehicle value at origination |
| CurrentVehicleValue | Current estimated vehicle value |

## FactLoanPerformance

| Field | Meaning |
| --- | --- |
| LoanID | Synthetic loan identifier |
| BorrowerID | Borrower relationship key |
| CurrentBalance | Current outstanding balance |
| DelinquencyDays | Current days past due |
| IFRS9_Stage | Synthetic Stage 1/2/3 label |
| PD_Estimate | Supplied synthetic PD estimate |
| LGD_Estimate | Supplied synthetic LGD estimate |
| EAD | Exposure at default |
| ECL_Provision | Supplied synthetic ECL provision |
| NetLoss | Net loss measure |

## Important data note

The portfolio is synthetic. PD, LGD, EAD, and ECL fields are supplied analytical fields in the sample data; the risk_modeling/pd_model.py script trains a baseline default classifier from origination-time features.
