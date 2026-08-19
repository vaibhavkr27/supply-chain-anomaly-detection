# %% [markdown]
# # Supply Chain Data Quality & Anomaly Detection
# Portfolio project for Data Analyst Intern application (Portcast-style role)
#
# Goal: load raw shipment data, check it for quality issues, flag anomalies,
# and summarize findings — mirroring real data-quality/QA analyst work.

# %% 1. IMPORTS
import pandas as pd
import numpy as np

# %% 2. LOAD THE DATA
df = pd.read_csv("delivery_logistics.csv")

print(df.shape)
df.head()

# %% 3. INITIAL INSPECTION
df.info()
df.describe()
df.columns.tolist()

# %% 3.5 FIX CORRUPTED TIME COLUMNS
# delivery_time_hours and expected_time_hours were exported from a
# spreadsheet as fake "1970-01-01 00:00:00.000000008"-style timestamps.
# The real value (e.g. 8) is hiding in the nanosecond digits after the dot.
# This is a genuine real-world data corruption issue — worth remembering
# for an interview as a concrete "I found something wrong and dug into why".

time_cols = ["delivery_time_hours", "expected_time_hours"]

for col in time_cols:
    # Safety check first: confirm every value actually matches the
    # corrupted-timestamp pattern before blindly converting.
    non_matching = df[~df[col].astype(str).str.match(r"^1970-01-01")]
    print(f"{col}: {len(non_matching)} rows do NOT match the corrupted pattern")
    if len(non_matching) > 0:
        print(non_matching[col].unique()[:10])

# If both printed 0 above, it's safe to extract the real numbers:
for col in time_cols:
    df[col] = df[col].str.extract(r"\.(\d+)$")[0].astype(int)

print("\nAfter fix:")
print(df[time_cols].describe())

# %% 4. DATA QUALITY CHECKS
# --- 4a. Missing values per column ---
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
quality_report = pd.DataFrame({"missing_count": missing, "missing_pct": missing_pct})
quality_report = quality_report[quality_report["missing_count"] > 0].sort_values(
    "missing_pct", ascending=False
)
print("Missing values by column:")
print(quality_report)

# --- 4b. Duplicate rows ---
dupe_count = df.duplicated().sum()
print(f"\nDuplicate rows: {dupe_count}")

# --- 4c. Impossible numeric values ---
numeric_col = "delivery_time_hours"
impossible = df[df[numeric_col] < 0]
print(f"\nRows with impossible negative {numeric_col}: {len(impossible)}")

# %% 5. CLEANING
df_clean = df.copy()

# Drop exact duplicates
df_clean = df_clean.drop_duplicates()

# Drop impossible negative values
df_clean = df_clean[df_clean[numeric_col] >= 0]

# Fill missing categorical values with "Unknown" rather than dropping
categorical_cols = df_clean.select_dtypes(include="object").columns
df_clean[categorical_cols] = df_clean[categorical_cols].fillna("Unknown")

print(f"Rows before cleaning: {len(df)}")
print(f"Rows after cleaning: {len(df_clean)}")

# %% 6. ANOMALY DETECTION — statistical outliers per carrier
carrier_col = "delivery_partner"

group_mean = df_clean.groupby(carrier_col)[numeric_col].transform("mean")
group_std = df_clean.groupby(carrier_col)[numeric_col].transform("std")

df_clean["z_score"] = (df_clean[numeric_col] - group_mean) / group_std
df_clean["is_anomaly"] = df_clean["z_score"].abs() > 2

anomalies = df_clean[df_clean["is_anomaly"]]
print(f"Anomalous shipments flagged: {len(anomalies)} out of {len(df_clean)}")

# %% 7. ROOT-CAUSE STYLE ANALYSIS
anomaly_rate_by_carrier = (
    df_clean.groupby(carrier_col)["is_anomaly"]
    .mean()
    .sort_values(ascending=False)
    .round(3)
)
print("Anomaly rate by carrier (higher = more unusually-timed deliveries):")
print(anomaly_rate_by_carrier)

# %% 8. SUMMARY REPORT
report = {
    "total_rows_raw": len(df),
    "total_rows_clean": len(df_clean),
    "duplicate_rows_removed": int(dupe_count),
    "negative_value_rows_removed": len(impossible),
    "anomalies_flagged": int(df_clean["is_anomaly"].sum()),
    "anomaly_rate_pct": round(df_clean["is_anomaly"].mean() * 100, 2),
}
report_df = pd.DataFrame([report])
report_df.to_csv("qa_report_summary.csv", index=False)
print(report_df)

# %% 9. SAVE CLEANED DATA (for loading into SQL next)
df_clean.to_csv("delivery_logistics_clean.csv", index=False)
print("Saved cleaned data to delivery_logistics_clean.csv")
# %%
# %% 10. INVESTIGATE TOP ANOMALIES (root cause, not just detection)
top_anomalies = df_clean[df_clean["is_anomaly"]].sort_values("z_score", ascending=False)
top_anomalies[[carrier_col, numeric_col, "z_score", "region", "weather_condition", "delivery_status"]].head(10)
# %%
