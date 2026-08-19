# Supply Chain Delivery Data Quality & Anomaly Detection

A data-quality and anomaly-detection pipeline built on a 25,000-row delivery
logistics dataset, mirroring real-world data analyst QA work: catching
corrupted data, flagging statistical anomalies, and investigating root
causes — not just reporting numbers.

## The Question
Delivery time data often looks "fine" at a glance but hides both formatting
corruption and real operational signals. Can a systematic pipeline catch
both — and can it explain *why* certain deliveries are unusually slow?

## Approach
1. **Load and inspect** 25,000 shipment records across 9 carriers
   (FedEx, DHL, Amazon Logistics, Blue Dart, Ekart, Xpressbees, Ecom
   Express, Shadowfax) and 6 weather conditions.
2. **Data quality checks** — missing values, duplicates, impossible
   (negative) values.
3. **Data corruption fix** — `delivery_time_hours` and `expected_time_hours`
   were exported from a spreadsheet as malformed timestamps (e.g.
   `1970-01-01 00:00:00.000000008` instead of the real value `8`). Verified
   the pattern held across all 25,000 rows before extracting the true
   values back out.
4. **Anomaly detection** — flagged shipments where delivery time was more
   than 2 standard deviations from the mean **for that specific carrier**
   (not a single global threshold, since normal delivery time varies by
   carrier).
5. **Cross-validation** — reproduced the exact same anomaly detection logic
   independently in SQL (CTEs + window functions: `AVG() OVER (PARTITION
   BY ...)`, `STDDEV() OVER (...)`) to confirm the Python result.
6. **Root-cause investigation** — didn't stop at "flagged," dug into what
   the anomalies had in common.

## Key Findings
- **25,000 rows processed, 0 duplicates, 0 negative values** — the dataset
  was otherwise clean once the timestamp corruption was fixed.
- **898 shipments (3.59%) flagged as statistical anomalies** — confirmed
  identically in both Python (pandas z-scores) and SQL (window functions):
  **898 = 898**, validating the logic two independent ways.
- **Root cause: weather.** Stormy conditions made up only **16.8%** of all
  shipments but **51.7%** of flagged anomalies — a **~3x over-representation**.
  Stormy + rainy combined explain **78.3%** of all anomalies while being
  only **33.5%** of shipments.

## Recommendation
Current scheduled delivery windows don't appear to account for weather
risk. A weather-adjusted SLA buffer (e.g., extending expected delivery
time during stormy/rainy forecasts) could reduce the number of shipments
that breach normal delivery expectations, and would let a data/ops team
distinguish genuine service failures from weather-driven delays — an
important distinction when evaluating carrier performance.

## Tech Stack
- **Python** (pandas) — data cleaning, corruption diagnosis, anomaly
  detection, root-cause analysis
- **SQL** (MySQL, CTEs, window functions) — independent validation of the
  same anomaly logic
- **Data:** [Delivery Logistics Dataset, Kaggle](https://www.kaggle.com/datasets/ayeshaseherr/delivery-logistics-dataset)

## Files
- `analysis.py` — full Python pipeline (cleaning → anomaly detection →
  root-cause analysis), structured as runnable notebook-style cells
- `queries.sql` — SQL version of the anomaly detection and root-cause
  queries
- `qa_report_summary.csv` — output summary of the cleaning/detection run
- `delivery_logistics_clean.csv` — cleaned dataset

## What I'd extend next
- A weather-adjusted SLA simulation — quantify how much the anomaly rate
  drops if expected delivery time is adjusted for forecasted weather
- A simple Power BI/Tableau dashboard visualizing anomaly rate by carrier,
  weather condition, and region
- Automate this pipeline to run on new data on a schedule
