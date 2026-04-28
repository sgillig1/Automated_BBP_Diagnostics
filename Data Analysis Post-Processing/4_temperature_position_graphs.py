#%% Imports
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

#%% Function to add event lines
def add_event_lines(ax, df, indices_dict, col='Time_min', color='0.3'):
    """Add subtle vertical lines for key events."""
    for label, idx in indices_dict.items():
        if idx is not None and idx < len(df):
            ax.axvline(
                x=df[col].iloc[idx],
                color=color,
                linestyle='--',
                linewidth=1
            )
            #### Optional: add text label above line
            # ax.text(
            #     df[col].iloc[idx],
            #     ax.get_ylim()[1] + 1,
            #     label.replace("_", " ").title(),
            #     rotation=90,
            #     fontsize=10,
            #     color=color,
            #     ha='center',
            #     va='bottom'
            # )

#%% Define indices dictionary (already found earlier)
indices = {
    'Start run': start_run_index,
    'Reach 50': reach_50_index,
    'Start 65': start_65_index,
    'Reach 65': reach_65_index
}

#%% Plot style
sns.set_theme() # Applies the default Seaborn theme
# or to set a specific style:
sns.set_style("whitegrid")
#plt.style.use('seaborn-whitegrid')  # clean white background with subtle grid
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'Arial',          # clean, readable font
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'lines.linewidth': 2,
    'axes.linewidth': 1.2,           # thicker axes
    'grid.color': '0.85',            # light gray grid
    'grid.linestyle': '--',
    'grid.linewidth': 0.7,
})

#%% 1️⃣ Temperature — Full data
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(df['Time_min'], df['Top_temp'], label='Top_temp', color='orange')
ax1.plot(df['Time_min'], df['Bot_Temp'], label='Bot_Temp', color='red')
ax1.plot(df['Time_min'], df['DHT_temp'], label='DHT_temp', color='purple')
ax1.plot(df['Time_min'], df['MLXObjectTemp'], label='MLXObjectTemp', color='blue')
ax1.plot(df['Time_min'], df['Top_set'], label='Top_set', linestyle=':', color='black')

ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Temp (˚C)')
ax1.set_ylim(20, 80)
add_event_lines(ax1, df, indices)
ax1.legend(loc='upper left')
plt.title(f'{exp_name}: Temperature')
plt.tight_layout()
plt.show()
fig_dict["Temperature"] = fig

#%% 2️⃣ Heating (focused between Amp_Status 2 and start 65)
time_amp_status_2 = df[df['Amp_Status'] == 2]['Time_min'].iloc[0]
time_amp_status_65 = df[(df['Amp_Status'] == 3) & (df['Top_set'] == 65)]['Time_min'].iloc[0]

df_filtered = df[(df['Time_min'] >= time_amp_status_2 - 5) &
                 (df['Time_min'] <= time_amp_status_65 + 5)]

fig, ax1 = plt.subplots(figsize=(10, 6))
for col, color in zip(['Top_temp', 'Bot_Temp', 'DHT_temp', 'MLXObjectTemp'], ['orange', 'red', 'purple', 'blue']):
    ax1.plot(df_filtered['Time_min'], df_filtered[col], label=col, color=color)
ax1.plot(df_filtered['Time_min'], df_filtered['Top_set'], label='Top_set', linestyle=':', color='black')

ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Temp (˚C)')
ax1.set_ylim(20, 80)
ax1.set_xticks(np.arange(int(df_filtered['Time_min'].min()), int(df_filtered['Time_min'].max()) + 1, 1))
ax1.legend(loc='upper left')
plt.xticks(rotation=45)
add_event_lines(ax1, df, indices)
plt.title(f'{exp_name}: Heating')
plt.tight_layout()
plt.show()
fig_dict["Heating"] = fig

#%% 3️⃣ Set Point 65
df_third_plot = df[df['Time_min'] >= time_amp_status_65 - 5]

fig, ax1 = plt.subplots(figsize=(10, 6))
for col, color in zip(['Top_temp', 'Bot_Temp', 'DHT_temp', 'MLXObjectTemp'], ['orange', 'red', 'purple', 'blue']):
    ax1.plot(df_third_plot['Time_min'], df_third_plot[col], label=col, color=color)
ax1.plot(df_third_plot['Time_min'], df_third_plot['Top_set'], label='Top_set', linestyle=':', color='black')

ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Temp (˚C)')
ax1.set_ylim(20, 80)
add_event_lines(ax1, df, indices)
ax1.legend(loc='upper left')
plt.title(f'{exp_name}: Set Point 65')
plt.tight_layout()
plt.show()
fig_dict["SetPoint"] = fig

#%% 4️⃣ Heating — Full Experiment
df_exp = df[df['Time_min'] >= time_amp_status_2 - 5]

fig, ax1 = plt.subplots(figsize=(10, 6))
for col, color in zip(['Top_temp', 'Bot_Temp', 'DHT_temp', 'MLXObjectTemp'], ['orange', 'red', 'purple', 'blue']):
    ax1.plot(df_exp['Time_min'], df_exp[col], label=col, color=color)
ax1.plot(df_exp['Time_min'], df_exp['Top_set'], label='Top_set', linestyle=':', color='black')

ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Temp (˚C)')
ax1.set_ylim(20, 80)
add_event_lines(ax1, df, indices)
ax1.legend(loc='lower right')
plt.title(f'{exp_name}: Experiment Heating')
plt.tight_layout()
plt.show()
fig_dict["ExpHeating"] = fig

#%% 5️⃣ Position Deviation
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(df['Time_min'], df['Position Deviation'], label="Deviation", color='black')
ax1.axhline(y=0.025, color='gray', linestyle='--', label='Threshold 0.025')
ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Position Deviation', color='black')
ax1.legend(loc='upper left')

ax2 = ax1.twinx()
ax2.plot(df['Time_min'], df['Position'], label='Position', color='red')
ax2.set_ylabel('Position', color='red')
add_event_lines(ax2, df, indices)
ax2.legend(loc='upper right')
plt.title(f'{exp_name}: Position Deviation Over Time')
plt.tight_layout()
plt.show()
fig_dict["PositionDeviation"] = fig

#%% 6️⃣ Position Over Time
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(df['Time_min'], df['Position'], label='Position', color='red')
ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Position')
add_event_lines(ax1, df, indices)
ax1.legend(loc='upper left')
plt.title(f'{exp_name}: Position Over Time')
plt.tight_layout()
plt.show()
fig_dict["Position"] = fig

#%% 6️⃣b Position Over Time (Y limit ±50)
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(df['Time_min'], df['Position'], label='Position', color='red')
ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Position')
# Limit y-axis to +/-50 to focus on typical position range
ax1.set_ylim(-5, 50)
add_event_lines(ax1, df, indices)
ax1.legend(loc='upper left')
plt.title(f'{exp_name}: Position Over Time (y limit ±50)')
plt.tight_layout()
plt.show()
fig_dict["Position_Ylim50"] = fig

#%% 7️⃣ Position + Well After Amp_Status 2
df_after_amp2 = df[df['Time_min'] >= time_amp_status_2]
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(df_after_amp2['Time_min'], df_after_amp2['Position'], color='red', label='Position')
ax2 = ax1.twinx()
ax2.plot(df_after_amp2['Time_min'], df_after_amp2['Well'], color='blue', label='Well')

ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Position', color='red')
ax2.set_ylabel('Well', color='blue')
add_event_lines(ax1, df, indices)
plt.title(f'{exp_name}: Position and Well After Amp Status 2')
plt.tight_layout()
plt.show()
fig_dict["PositionWellAfterAmpStatus2"] = fig

#%% 8️⃣ Heat, Lid, Amp, and Error Status
fig, ax1 = plt.subplots(figsize=(10, 6))

# Existing status lines
ax1.plot(df['Time_min'], df['Heat_Status'], color='green', label='Heat_Status')
ax1.plot(df['Time_min'], df['Lid_Status'], color='blue', label='Lid_Status')
ax1.plot(df['Time_min'], df['Amp_Status'], color='purple', label='Amp_Status')

# New Error_Status line
ax1.plot(df['Time_min'], df['Error_Status'], color='red', linestyle='--', label='Error_Status')

ax1.set_xlabel('Time Elapsed (min)')
ax1.set_ylabel('Status / Error')
ax1.set_ylim(-1, 4)  # Extend to fit the error codes
add_event_lines(ax1, df, indices)
ax1.legend(loc='upper left')
plt.title(f'{exp_name}: Heat, Lid, Amp, and Error Status Over Time')

status_note = """
Heat Status
0. Not initialized
1. No heat
2. Heat
3. Reach set point

Amp Status
0. Not initialized
1. Pre-Heat (no fluorescence)
2. Amplification (fluorescence)
3. Amplification (reached temp, Bob algorithm)

Error Status
0 = no errors
1 = heating
2 = motor
3 = both
"""
plt.figtext(0.25, -0.2, status_note.split('\n\n')[0], ha='center', fontsize=10)
plt.figtext(0.55, -0.2, status_note.split('\n\n')[1], ha='center', fontsize=10)
plt.figtext(0.85, -0.2, status_note.split('\n\n')[2], ha='center', fontsize=10)

plt.tight_layout()
plt.show()
fig_dict["HeatLidAmpErrorStatus"] = fig