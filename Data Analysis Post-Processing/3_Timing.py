#%% --- Imports ---
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
from matplotlib.ticker import MultipleLocator

#%% --- Timing Analysis ---

# Ensure df exists
if 'df' not in globals():
    raise NameError("DataFrame 'df' not found. Run 1_Setup.py and 2_Data_Process.py first.")

# Ensure metadata exists
if 'exp_dir' not in globals():
    exp_dir = os.getcwd()
if 'exp_name' not in globals():
    exp_name = "experiment"
if 'today_date' not in globals():
    today_date = datetime.now().strftime("%Y-%m-%d")

# Add derived columns
df['Position Well'] = (df['Position'].abs() % 1).round(3) * 4
df['Position Deviation'] = df.apply(
    lambda row: 0 if row['Well'] == 0 else round(abs(row['Position Well'] - round(row['Position Well'])) / 4, 3),
    axis=1
)

# Initialize event tracking
time_tracking = {
    "Event": [
        "Start of Preheat",
        "Start Run",
        "Reach 50°C",
        "Time Between Start Run and Reach 50°C",
        "Start 65°C",
        "Reach 65°C",
        "Time Between Start 65°C and Reach 65°C"
    ],
    "Time Elapsed (min)": [None] * 7,
    "Timestamp": [None] * 7
}

def find_index(condition):
    """Return the first index that satisfies a condition or None."""
    matches = df.index[condition]
    return matches[0] if len(matches) > 0 else None

# Find event indices (unchanged)
start_preheat_index = find_index(df['Amp_Status'] == 1)
start_run_index     = find_index(df['Amp_Status'] == 2)
reach_50_index      = find_index((df.index > start_run_index) & (df['MLXObjectTemp'] >= 50))
start_65_index      = find_index((df.index > reach_50_index) & (df['Top_set'] == 65))
reach_65_index      = find_index((df.index > start_65_index) & (df['MLXObjectTemp'] >= 65))

# DEBUG: print found indices (helps see 0/None)
print("DEBUG indices:",
      f"start_preheat={start_preheat_index}",
      f"start_run={start_run_index}",
      f"reach_50={reach_50_index}",
      f"start_65={start_65_index}",
      f"reach_65={reach_65_index}")

# Fill timing table safely.
# The time_tracking["Event"] ordering is:
# 0 Start of Preheat
# 1 Start Run
# 2 Reach 50°C
# 3 Time Between Start Run and Reach 50°C (computed)
# 4 Start 65°C
# 5 Reach 65°C
# 6 Time Between Start 65°C and Reach 65°C (computed)

# Assign the raw event timestamps to the correct indices in the table
event_indices = [start_preheat_index, start_run_index, reach_50_index, start_65_index, reach_65_index]
# map them to table positions 0,1,2,4,5 respectively
table_positions = [0, 1, 2, 4, 5]

for pos, idx in zip(table_positions, event_indices):
    if idx is not None:
        time_tracking["Time Elapsed (min)"][pos] = df.loc[idx, 'Time_min']
        time_tracking["Timestamp"][pos] = df.iloc[idx, 0]

# Add computed intervals using explicit None checks (handles index == 0)
if (start_run_index is not None) and (reach_50_index is not None):
    interval = df.loc[reach_50_index, 'Time_min'] - df.loc[start_run_index, 'Time_min']
    time_tracking["Time Elapsed (min)"][3] = interval
    time_tracking["Timestamp"][3] = ""  # optional

if (start_65_index is not None) and (reach_65_index is not None):
    interval = df.loc[reach_65_index, 'Time_min'] - df.loc[start_65_index, 'Time_min']
    time_tracking["Time Elapsed (min)"][6] = interval
    time_tracking["Timestamp"][6] = ""  # optional

# Convert to DataFrame and print
time_tracking_df = pd.DataFrame(time_tracking)
print("\n===== Timing Events =====")
print(time_tracking_df)

#%% --- Save output ---
out_path = os.path.join(exp_dir, f"{today_date}_{exp_name}_time_tracking.csv")
time_tracking_df.to_csv(out_path, index=False)
print(f"\nSaved timing data → {out_path}")