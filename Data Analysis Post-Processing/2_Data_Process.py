#%% Convert Time to minutes (Time in ms from start)
# df['Time'] = pd.to_numeric(df['Time'], errors='coerce')  # ensure numeric
# df['Time_min'] = df['Time'] / 1000 / 60  # ms → seconds → minutes

# Detect the 2nd column (usually timestamp like '2025-10-14 14:23:57')
time_col = df.columns[0]
# Convert to datetime
df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
# Calculate elapsed minutes relative to the first timestamp
df['Time_min'] = (df[time_col] - df[time_col].iloc[0]).dt.total_seconds() / 60

# Add 'Position Well' column
df['Position Well'] = (df['Position'].abs() % 1).round(3)*4  # round to 3 decimals

# Add 'Position Deviation' column
df['Position Deviation'] = df.apply(
    lambda row: 0
        if row['Well'] == 0
        else round(abs(row['Position Well'] - round(row['Position Well'])) / 4, 3),
    axis=1
)

df['TEX/LED'] 


# Split DataFrame by Well and LED_Status
groups = df.groupby(['Well', 'LED_Status'])
dfs_split = {(well, led): g for (well, led), g in groups}
print(f"Created {len(dfs_split)} sub-DataFrames based on Well and LED_Status.")

# Extract time + temperature from same subset (avoid shape mismatch)
temp_df = df.loc[df['Well'] != 0, ['Time_min', 'MLXObjectTemp']].dropna(subset=['Time_min', 'MLXObjectTemp'])

time = temp_df['Time_min'].to_numpy()
temperature = pd.to_numeric(temp_df['MLXObjectTemp'], errors='coerce').to_numpy()

#%% Split DataFrame by Well and LED_Status
groups = df.groupby(['Well', 'LED_Status'])
dfs_split = {(well, led): g for (well, led), g in groups}
print(f"Created {len(dfs_split)} sub-DataFrames based on Well and LED_Status.")

#%% Separate subgroups
fam_dfs = [g for (well, led), g in dfs_split.items() if led == 1 and well != 0]
tex_dfs = [g for (well, led), g in dfs_split.items() if led == 2 and well != 0]