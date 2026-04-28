#%%
from scipy.optimize import curve_fit
from matplotlib import cm

# Secondary x-axis using start_65_index
start_65_time = df.loc[start_65_index, 'Time_min']

# Function to convert main time -> time since start_65
def time_since_65(x):
    return x - start_65_time

#%%
def add_vertical_line(ax, x_value, color='gray', linestyle='--', label='Start 65'):
    """
    Adds a vertical line to the given axis.

    Parameters:
        ax (matplotlib.axes.Axes): The axis to draw the line on.
        x_value (float): The x-position to place the vertical line.
        color (str): Line color.
        linestyle (str): Line style (default dashed).
        label (str): Label for the legend.
    """
    ax.axvline(x=x_value, color=color, linestyle=linestyle, label=label)

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

#%% Find start of run (first occurrence of Amp_Status 2)
# Restrict data to start_run_index forward
df_fluor = df.iloc[start_run_index:].copy()
time = df_fluor['Time_min']
temperature = df_fluor['MLXObjectTemp']

fam_dfs_filtered = [sub_df[sub_df['Time_min'] >= time.iloc[0]] for sub_df in fam_dfs]
tex_dfs_filtered = [sub_df[sub_df['Time_min'] >= time.iloc[0]] for sub_df in tex_dfs]

# Parameters for smoothing
window = 20
z_thresh = 2

# Parameters for smoothing TEX
window_TEX = 20
z_thresh_TEX = 2

# THis interpolates as well which changes the data
# def remove_outliers(series, window=window, z_thresh=z_thresh):
#     """Removes spikes based on z-score relative to a rolling median."""
#     rolling_median = series.rolling(window=window, center=True, min_periods=1).median()
#     diff = series - rolling_median
#     z = np.abs((diff - diff.mean()) / diff.std())
#     cleaned = series.copy()
#     cleaned[z > z_thresh] = np.nan
#     return cleaned.interpolate()

def remove_outliers(series, window=window, z_thresh=z_thresh):
    """Removes spikes based on z-score relative to a rolling median.
    Outliers are replaced with NaN (no interpolation)."""
    rolling_median = series.rolling(window=window, center=True, min_periods=1).median()
    diff = series - rolling_median
    z = np.abs((diff - diff.mean()) / diff.std())

    cleaned = series.copy()
    cleaned[z > z_thresh] = np.nan  # Replace outliers with NaN
    return cleaned

#%% --- Raw FAM Signals ---
fig, ax1 = plt.subplots(figsize=(12,6))
for i, sub_df in enumerate(fam_dfs_filtered):
    well = sub_df['Well'].iloc[0]
    color = colors[i % 4]  # cycle through colors if more than 4 wells
    ax1.plot(sub_df['Time_min'], sub_df['FAM/LED'], label=f'Well {well}', color=color)

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('FAM/LED (Raw)')
ax1.grid(True)

ax2 = ax1.twinx()
ax2.plot(time, temperature, color='tab:red', label='MLXObjectTemp')
ax2.set_ylabel('MLXObjectTemp (°C)')
# Left y-axis grid only
ax1.grid(True)
ax2.grid(False)  # prevent temperature axis from drawing grid

add_vertical_line(ax1, start_65_time)

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
plt.title(f'{exp_name}: All FAM Signals (Raw)')
plt.tight_layout()
plt.show()
fig_dict["FAM_Fluorescence_Raw"] = fig

#%% --- Raw TEX Signals ---
fig, ax1 = plt.subplots(figsize=(12,6))
for i, sub_df in enumerate(tex_dfs_filtered):
    well = sub_df['Well'].iloc[0]
    color = colors[i % 4]  # cycle through colors if more than 4 wells
    ax1.plot(sub_df['Time_min'], sub_df['TEX/LED'], label=f'Well {well}', color=color)

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('TEX/LED (Raw)')
ax1.grid(True)
plt.ylim(0.04,0.1)

ax2 = ax1.twinx()
ax2.plot(time, temperature, color='tab:red', label='MLXObjectTemp')
ax2.set_ylabel('MLXObjectTemp (°C)')
# Left y-axis grid only
ax1.grid(True)
ax2.grid(False)  # prevent temperature axis from drawing grid

add_vertical_line(ax1, start_65_time)

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
plt.title(f'{exp_name}: All TEX Signals (Raw)')
plt.tight_layout()
plt.show()
fig_dict["TEX_Fluorescence_Raw"] = fig

#%% --- Filtered FAM Signals ---
fig, ax1 = plt.subplots(figsize=(12,6))
for i, sub_df in enumerate(fam_dfs_filtered):
    well = sub_df['Well'].iloc[0]
    color = colors[i % 4]  # cycle through colors if more than 4 wells
    y = remove_outliers(sub_df['FAM/LED'])
    y_smooth = y.rolling(window=window, center=True, min_periods=1).mean()
    ax1.plot(sub_df['Time_min'], y_smooth, label=f'Well {well}', color=color)

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('FAM/LED (Filtered)')
ax1.grid(True)

ax2 = ax1.twinx()
ax2.plot(time, temperature, color='tab:red', label='MLXObjectTemp')
ax2.set_ylabel('MLXObjectTemp (°C)')
# Left y-axis grid only
ax1.grid(True)
ax2.grid(False)  # prevent temperature axis from drawing grid

add_vertical_line(ax1, start_65_time)

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
plt.title(f'{exp_name}: All FAM Signals (Filtered)')
plt.tight_layout()
plt.show()
fig_dict["FAM_Fluorescence_Filtered"] = fig

#%% --- Filtered TEX Signals ---
fig, ax1 = plt.subplots(figsize=(12,6))
for i, sub_df in enumerate(tex_dfs_filtered):
    well = sub_df['Well'].iloc[0]
    color = colors[i % 4]  # cycle through colors if more than 4 wells
    y = remove_outliers(sub_df['TEX/LED'], window_TEX, z_thresh_TEX)
    y_smooth = y.rolling(window=window, center=True, min_periods=1).mean()
    ax1.plot(sub_df['Time_min'], y_smooth, label=f'Well {well}', color=color)

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('TEX/LED (Filtered)')
ax1.grid(True)

ax2 = ax1.twinx()
ax2.plot(time, temperature, color='tab:red', label='MLXObjectTemp')
ax2.set_ylabel('MLXObjectTemp (°C)')
# Left y-axis grid only
ax1.grid(True)
ax2.grid(False)  # prevent temperature axis from drawing grid

add_vertical_line(ax1, start_65_time)

lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
plt.title(f'{exp_name}: All TEX Signals (Filtered)')
plt.tight_layout()
plt.show()
fig_dict["TEX_Fluorescence_Filtered"] = fig

#%% --- Combined Unfiltered (low opacity) + Filtered (solid) FAM ---
fig, ax1 = plt.subplots(figsize=(12,6))
for i, sub_df in enumerate(fam_dfs_filtered):
    # Restrict to start_65_time onward
    sub_df_plot = sub_df[sub_df['Time_min'] >= start_65_time]
    if sub_df_plot.empty:
        continue

    well = sub_df_plot['Well'].iloc[0]
    color = colors[i % 4]

    # Unfiltered (raw) - low opacity
    y_raw = sub_df_plot['FAM/LED']
    ax1.plot(sub_df_plot['Time_min'], y_raw, label=f'Well {well} Raw', color=color, alpha=0.25)

    # Filtered (no interpolation) - solid
    y_clean = remove_outliers(y_raw)
    y_smooth = y_clean.rolling(window=window, center=True, min_periods=1).mean()
    ax1.plot(sub_df_plot['Time_min'], y_smooth, label=f'Well {well} Filtered', color=color)

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('FAM/LED')
ax1.grid(True)
ax1.legend(loc='upper left', ncol=2)
plt.title(f'{exp_name}: FAM - Unfiltered (low alpha) + Filtered')
plt.tight_layout()
plt.show()
fig_dict["FAM_Unfiltered_and_Filtered"] = fig

#%% --- Combined Unfiltered (low opacity) + Filtered (solid) TEX ---
fig, ax1 = plt.subplots(figsize=(12,6))
for i, sub_df in enumerate(tex_dfs_filtered):
    # Restrict to start_65_time onward
    sub_df_plot = sub_df[sub_df['Time_min'] >= start_65_time]
    if sub_df_plot.empty:
        continue

    well = sub_df_plot['Well'].iloc[0]
    color = colors[i % 4]

    # Unfiltered (raw) - low opacity
    y_raw = sub_df_plot['TEX/LED']
    ax1.plot(sub_df_plot['Time_min'], y_raw, label=f'Well {well} Raw', color=color, alpha=0.25)

    # Filtered (no interpolation) - solid
    y_clean = remove_outliers(y_raw, window_TEX, z_thresh_TEX)
    y_smooth = y_clean.rolling(window=window_TEX, center=True, min_periods=1).mean()
    ax1.plot(sub_df_plot['Time_min'], y_smooth, label=f'Well {well} Filtered', color=color)

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('TEX/LED')
ax1.grid(True)
ax1.legend(loc='upper left', ncol=2)
plt.ylim(0.04,0.1)
plt.title(f'{exp_name}: TEX - Unfiltered (low alpha) + Filtered')
plt.tight_layout()
plt.show()
fig_dict["TEX_Unfiltered_and_Filtered"] = fig

#%% --- Filtered Amplification ---
fig, ax1 = plt.subplots(figsize=(12,6))
for i, sub_df in enumerate(fam_dfs_filtered):
    well = sub_df['Well'].iloc[0]
    color = colors[i % 4]  # cycle through colors if more than 4 wells
    y = remove_outliers(sub_df['FAM/LED'])
    y_smooth = y.rolling(window=window, center=True, min_periods=1).mean()
    ax1.plot(sub_df['Time_min'], y_smooth, label=f'Well {well}', color=color)

ax1.set_xlabel('Time (minutes)')
ax1.set_ylabel('FAM/LED (Filtered)')
ax1.grid(False)


ax2 = ax1.twinx()
ax2.set_ylabel('TEX/LED (Filtered)')
plt.ylim(0.04, 0.1)

for i, sub_df in enumerate(tex_dfs_filtered):
    well = sub_df['Well'].iloc[0]
    color = colors[i % 4]  # cycle through colors if more than 4 wells
    y = remove_outliers(sub_df['TEX/LED'], window_TEX, z_thresh_TEX)
    y_smooth = y.rolling(window=window_TEX, center=True, min_periods=1).mean()
    ax2.plot(sub_df['Time_min'], y_smooth, label=f'Well {well}', color=color, ls='--')

# Left y-axis grid only
ax2.grid(False)  # prevent temperature axis from drawing grid

add_vertical_line(ax1, start_65_time)

lines_1, labels_1 = ax1.get_legend_handles_labels()
#lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
plt.title(f'{exp_name}: Amplification (Filtered)')
plt.tight_layout()
plt.show()
fig_dict["Fluorescence_Filtered"] = fig

#%% --- Fitting Function ---

# 4-parameter logistic function
def logistic4(x, A, B, C, D):
    """
    4-parameter logistic function:
    y = A + (B - A) / (1 + (x/C)**D)
    A: minimum
    B: maximum
    C: midpoint
    D: slope
    """
    return A + (B - A) / (1 + (x / C) ** D)

# Plot function
def plot_with_fit_fixed_colors(dfs_filtered, signal_col, exp_name, fig_dict):
    fig, ax1 = plt.subplots(figsize=(12,6))

    # Fixed colors for 4 wells (define somewhere above this function)
    # colors = ['tab:blue', 'tab:orange', 'tab:green', 'black']

    for i, sub_df in enumerate(dfs_filtered):
        well = sub_df['Well'].iloc[0]
        color = colors[i % 4]  # cycle through colors if more than 4 wells

        # Raw signal as faint background
        y = sub_df[signal_col]
        ax1.plot(sub_df['Time_min'], y, color=color, alpha=0.3)

        # Fit curve
        try:
            mask = np.isfinite(y)
            t_mid = sub_df['Time_min'].iloc[len(sub_df)//2]  # midpoint of time
            p0 = [min(y), max(y), t_mid, 1]  # initial guess: A, B, C, D

            popt, _ = curve_fit(
                logistic4,
                sub_df['Time_min'][mask],
                y[mask],
                p0=p0,
                maxfev=5000
            )
            t_fit = np.linspace(sub_df['Time_min'].min(), sub_df['Time_min'].max(), 200)
            y_fit = logistic4(t_fit, *popt)
            ax1.plot(t_fit, y_fit, label=f'Well {well} Fit', color=color, linewidth=2)
        except Exception as e:
            print(f"Fit failed for Well {well}: {e}")

    # Axis labels and grid
    ax1.set_xlabel('Time (minutes)')
    ax1.set_ylabel(f'{signal_col} (Fitted)')
    ax1.grid(True)

    add_vertical_line(ax1, start_65_time)

    # Temperature overlay
    ax2 = ax1.twinx()
    ax2.plot(time, temperature, color='tab:red', label='MLXObjectTemp')
    ax2.set_ylabel('MLXObjectTemp (°C)')
    ax2.grid(False)

    # Combined legend
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

    # Title and layout
    plt.title(f'{exp_name}: {signal_col} Signals with Fit')
    plt.tight_layout()

    # Safe key for fig_dict
    safe_key = f"{signal_col.replace('/', '_')}_Fluorescence_Fit"
    fig_dict[safe_key] = fig

    plt.show()

# --- Plot FAM ---
plot_with_fit_fixed_colors(fam_dfs_filtered, 'FAM/LED', exp_name, fig_dict)

# --- Plot TEX ---
plot_with_fit_fixed_colors(tex_dfs_filtered, 'TEX/LED', exp_name, fig_dict)
# %%
for sub_df in fam_dfs_filtered:
    y = remove_outliers(sub_df['FAM/LED'])
    sub_df['FAM_filtered'] = y.rolling(window=window, center=True, min_periods=1).mean()

for sub_df in tex_dfs_filtered:
    y = remove_outliers(sub_df['TEX/LED'], window_TEX, z_thresh_TEX)
    sub_df['TEX_filtered'] = y.rolling(window=window_TEX, center=True, min_periods=1).mean()
