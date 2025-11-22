# Behavior Scorecard — Power BI Template Kit (Option A: Basic Scorecard)

**What this kit contains (everything you need to recreate a .PBIT-style dashboard):**

1. `powerbi_predict.py` — Python scoring script Power BI will call.
2. `sample_behavior_scorecard.csv` — A small sample dataset you can import (CSV / Excel).
3. `Power BI Theme (JSON)` — Visual theme (banking colors) to import into Power BI.
4. DAX measures & Risk Category formula to paste into Power BI.
5. Step-by-step build instructions (import data, enable Python, add visuals, wire script).

---

## 1) `powerbi_predict.py` (Place in same folder as model files)

```python
# powerbi_predict.py
# Power BI calls this script via the "Python script" data connector.
# It expects a pandas.DataFrame named `dataset` passed in by Power BI.

import pandas as pd
import joblib
import math
import os

# Adjust filenames as needed
MODEL_FILE = "behavior_model.pkl"   # your SMOTE-trained model or final model (joblib/pickle)
SCALER_FILE = "scaler.pkl"         # optional; if not used, set to None

# Load once (Power BI runs the script each refresh)
_model = None
_scaler = None

if os.path.exists(MODEL_FILE):
    _model = joblib.load(MODEL_FILE)
else:
    raise FileNotFoundError(f"Model file not found: {MODEL_FILE}")

if os.path.exists(SCALER_FILE):
    _scaler = joblib.load(SCALER_FILE)

# Scorecard constants (tweak as you used during design)
SCORE_REF = 600
PDO = 20
ODDS = 20

B = PDO / math.log(2)
A = SCORE_REF + B * math.log(ODDS)

def compute_score(pd):
    pd = max(0.001, min(0.999, pd))
    odds = pd / (1 - pd)
    return A - B * math.log(odds)

# Power BI provides a DataFrame named `dataset` to this script.
# Ensure the columns in `dataset` match the model's training features order.

def powerbi_predict(dataset: pd.DataFrame) -> pd.DataFrame:
    X = dataset.copy()

    # If you used a scaler, apply it
    if _scaler is not None:
        X_values = _scaler.transform(X.values)
    else:
        X_values = X.values

    # Predict PD
    pd_probs = _model.predict_proba(X_values)[:, 1]

    # Add outputs
    dataset_out = dataset.copy()
    dataset_out["PD"] = pd_probs
    dataset_out["Behavior_Score"] = [compute_score(p) for p in pd_probs]
    dataset_out["Risk_Category"] = dataset_out["Behavior_Score"].apply(
        lambda s: "Low" if s >= 700 else ("Medium" if s >= 600 else "High")
    )

    return dataset_out

# When invoked from Power BI, call powerbi_predict(dataset) and assign to `df`.
# Example (inside Power BI's Python script editor):
# from powerbi_predict import powerbi_predict
# df = powerbi_predict(dataset)
```

---

## 2) `sample_behavior_scorecard.csv` (columns & sample rows)

This CSV is intentionally minimal — Option A requires only feature columns the model expects.
Replace with your real feature list in the same order as you trained the model.

```
CustomerID,feature_1,feature_2,feature_3,feature_4
CUST_001,0.12,45000,0.30,1
CUST_002,0.05,32000,0.10,0
CUST_003,0.20,27000,0.55,2
CUST_004,0.02,100000,0.05,0
CUST_005,0.15,52000,0.40,1
```

> **Important:** `feature_1..feature_n` must match the input features and order used when training `behavior_model.pkl`.

---

## 3) Power BI Theme JSON (Banking palette)

Save this as `pb_theme_bank.json` and import in Power BI: View → Themes → Browse for themes.

```json
{
  "name": "Behavior Scorecard - Banking",
  "dataColors": ["#28A745", "#F0AD4E", "#D73A49", "#3A4A5B", "#6C757D"],
  "background": "#FFFFFF",
  "foreground": "#222222",
  "tableAccent": "#3A4A5B"
}
```

---

## 4) DAX Measure: Risk Category (if you prefer DAX over Python label)

If you already have `Behavior_Score` column from Python, you can add this DAX column:

```DAX
Risk Category =
SWITCH(
    TRUE(),
    'Table'[Behavior_Score] >= 700, "Low",
    'Table'[Behavior_Score] >= 600, "Medium",
    "High"
)
```

(Replace `'Table'` with your actual table name.)

---

## 5) Step-by-step (Recreate the PBIT in Power BI in ~20–25 minutes)

### A. Folder & files setup

1. Create a folder `behavior_scorecard_powerbi`.
2. Put these files in it: `powerbi_predict.py`, `behavior_model.pkl`, `scaler.pkl` (if any), `sample_behavior_scorecard.csv`, `pb_theme_bank.json`.

### B. Open Power BI Desktop

1. File → Options and settings → Options → Python scripting: set Python home (Anaconda path).
2. Home → Get Data → Text/CSV → Select `sample_behavior_scorecard.csv` → Load.

### C. Call the Python scoring script

1. Home → Get Data → More → Other → Python script → Connect.
2. In the Python script box paste:

```python
from powerbi_predict import powerbi_predict

df = powerbi_predict(dataset)
```

3. Power BI runs the script and returns `df` with `PD`, `Behavior_Score`, `Risk_Category`.

> Note: Power BI passes `dataset` automatically (the loaded table). Ensure the column order matches training.

### D. Model columns & data types

1. In Power Query, ensure numeric columns are Decimal Number.
2. `Behavior_Score` set to Decimal Number, PD set to Decimal Number, `Risk_Category` set to Text.

### E. Theme

1. View → Themes → Browse for themes → import `pb_theme_bank.json`.

### F. Build Visuals (drag & drop)

**Page 1 — Executive Overview**

* KPI card: Avg Behavior Score → `Average(Behavior_Score)`
* KPI card: Avg PD → `Average(PD)`
* KPI card: Total Customers = `COUNTROWS('Table')`
* Donut chart: Legend = `Risk_Category`, Values = `Count of CustomerID`
* Histogram: PD distribution → use `PD` on X (bin), Count on Y
* Histogram: Score distribution → `Behavior_Score` binned
* Table: Top 10 High Risk → CustomerID, PD, Behavior_Score sorted by PD desc

### G. Publish

1. Save PBIX.
2. Publish to Power BI Service.
3. If scheduled refresh required for on-prem files, set up an On-prem data gateway and ensure Python is available on gateway machine.

---

## 6) Troubleshooting & Tips

* **Feature order mismatch**: The most common issue — confirm the same column order used in training. If needed, re-generate `sample_behavior_scorecard.csv` from your training DataFrame columns order.
* **Missing model file**: Power BI’s Python environment must have access to `behavior_model.pkl` and `scaler.pkl` in the same folder where you launched Power BI.
* **Python package errors**: Make sure scikit-learn and joblib versions in the Power BI Python environment match those used to train the model.

---

## 7) Optional extras (if you want later)

* Add a What-If parameter slider and call Python to re-score (simulate changes). This requires adding a small input table and re-running the Python script.
* Export a simple report PDF for your project using Power BI’s Export function.

---

## 8) Deliverables I can provide next (pick any):

* A ready-to-copy `powerbi_predict.py` as a single downloadable file.
* A complete sample CSV with 500 synthetic rows matching your feature schema.
* Step-by-step video walkthrough (short screencast).

Tell me which extra files you want and I will prepare them.
