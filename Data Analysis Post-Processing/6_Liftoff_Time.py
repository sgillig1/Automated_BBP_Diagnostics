"""
6_Liftoff_Time.py

Compute "real time call" (detection) and signal-to-noise metrics for each
fluorescence well (FAM and TEX), export rolling averages, and plot traces.

Detection:
- Uses FILTERED signal if available:
    FAM: column 'FAM_filtered' (fallback to 'FAM/LED' if missing)
    TEX: column 'TEX_filtered' (fallback to 'TEX/LED' if missing)

Metrics (per well, per LED):
- SNR_RMS_raw:     RMS(signal window, RAW) / RMS(noise window, RAW)
- SNR_dynamic_raw: (peak(signal window, RAW) - mean(noise window, RAW)) / RMS(noise, RAW)
- SNR_RMS_filt:    RMS(signal window, FILTERED) / RMS(noise window, FILTERED)
- SNR_dynamic_filt:(peak(signal window, FILTERED) - mean(noise window, FILTERED)) / RMS(noise, FILTERED)

Outputs
1) Summary CSV (per well):
   <today>_<exp_name>_rt_snr.csv
   Columns:
   - Well
   - LED
   - Detection_Time_min_since_65   (time relative to start_65_time, based on FILTERED signal)
   - Detection_Index               (index in time_main for detection, FILTERED)
   - Signal_RMS_raw
   - Noise_RMS_raw
   - SNR_RMS_raw
   - SNR_dynamic_raw
   - Signal_RMS_filt
   - Noise_RMS_filt
   - SNR_RMS_filt
   - SNR_dynamic_filt
   - Multiplier

2) Rolling CSV (wide, per timepoint; FILTERED signal only):
   <today>_<exp_name>_rolling_avgs.csv
   Columns:
   - Time_min_since_65
   - FAM_W<well>_Signal        (FILTERED)
   - FAM_W<well>_Rolling_Short (FILTERED)
   - FAM_W<well>_Rolling_Long  (FILTERED)
   - TEX_W<well>_Signal        (FILTERED)
   - TEX_W<well>_Rolling_Short (FILTERED)
   - TEX_W<well>_Rolling_Long  (FILTERED)

Additionally:
- For each (well, LED), show a plot (not saved) with:
    x-axis: Time since start_65 (min)
    y-axis: FILTERED Signal and rolling averages
    Rolling_Long × multiplier threshold
    Vertical dashed line at positive call time (FILTERED).
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt  # for plotting

# --- Safety checks for required globals ---
required = ['time_main', 'start_65_time', 'fam_dfs_filtered', 'tex_dfs_filtered',
            'exp_dir', 'exp_name', 'today_date']
missing = [r for r in required if r not in globals()]
if missing:
    raise NameError(
        f"Missing required globals to run 6_Liftoff_Time.py: {missing}. "
        "Run the previous steps via the orchestrator or `%run -i`."
    )

# Bring globals into local scope
time_main = np.array(time_main)   # numpy array of Time_min used for fluorescence export
start_65_time = float(start_65_time)

# Time relative to start_65_time (used for all outputs & plots)
time_rel = time_main - start_65_time

# Parameters (tweak if desired)
short_window_min = 2.0          # last 2 minutes (rolling short average)
long_window_start_min = -7.0    # start of long baseline window (minutes relative to current t)
long_window_end_min = -6.0      # end of long baseline window (minutes relative to current t)

multiplier = {
    'FAM': 1.25, # 1.5 is good, but 1.25 for more noise
    'TEX': 1.1
}

# SNR windows (relative to start_65_time)
snr_noise_start  = 15.0   # minutes after start_65
snr_noise_end    = 20.0
snr_signal_start = 65
snr_signal_end   = 70.0

# Ignore early time for positive call (minutes after start_65_time)
detection_ignore_min = 12.0

summary_rows = []

# Wide rolling dataframe (one column per well/metric; FILTERED signal)
rolling_wide_df = pd.DataFrame({
    'Time_min_since_65': time_rel
})

# --- helpers ---

def align_to_main_time(sub_df, time_col='Time_min', signal_col='FAM/LED'):
    """
    Align a per-well signal column onto the global time_main axis.
    """
    s = pd.Series(sub_df[signal_col].values,
                  index=sub_df[time_col]).reindex(time_main)
    return np.array(s)  # may contain np.nan


def compute_detection_and_snr(signal_arr, t_arr, start_time, led_label):
    """
    Detection + SNR on a single signal array (used for FILTERED signal).

    signal_arr: numpy array aligned to t_arr (same length), may contain NaN
    t_arr: numpy array of times (minutes, absolute)
    start_time: scalar (absolute minutes, start_65_time)
    led_label: 'FAM' or 'TEX'

    returns: dict with detection_time_min (absolute), detection_index (int or -1),
             signal_rms, noise_rms, snr_rms, snr_dynamic,
             rolling_short (array), rolling_long (array).
    """
    n = len(t_arr)
    rolling_short = np.full(n, np.nan)
    rolling_long  = np.full(n, np.nan)
    positive      = np.zeros(n, dtype=int)

    # --- detection logic ---
    for i in range(n):
        t = t_arr[i]

        # short window: t - short_window_min <= t_j <= t
        mask_short = (t_arr - t >= -short_window_min) & (t_arr - t <= 0)
        vals_short = signal_arr[mask_short]
        rolling_short[i] = np.nanmean(vals_short) if not np.isnan(vals_short).all() else np.nan

        # long baseline window (relative offset)
        mask_long = (t_arr - t >= long_window_start_min) & (t_arr - t <= long_window_end_min)
        vals_long = signal_arr[mask_long]
        rolling_long[i] = np.nanmean(vals_long) if not np.isnan(vals_long).all() else np.nan

        # positive flag if both exist and short > long * multiplier
        if not np.isnan(rolling_short[i]) and not np.isnan(rolling_long[i]):
            if rolling_short[i] > rolling_long[i] * multiplier.get(led_label, 1.5):
                positive[i] = 1

    # Find first positive index, but ignore the first detection_ignore_min after start_65
    call_start_time = start_time + detection_ignore_min
    indices_after_start = np.where(t_arr >= call_start_time)[0]

    detection_index = -1
    detection_time  = np.nan
    if indices_after_start.size > 0:
        for idx in indices_after_start:
            if positive[idx] == 1:
                detection_index = int(idx)
                detection_time  = float(t_arr[idx])
                break

    # --- SNR calculations on this signal (FILTERED) ---

    # Noise window (absolute times, defined relative to start_time)
    noise_mask = (t_arr >= (start_time + snr_noise_start)) & (t_arr <= (start_time + snr_noise_end))
    noise_vals = signal_arr[noise_mask]
    noise_vals = noise_vals[~np.isnan(noise_vals)]

    if noise_vals.size == 0:
        noise_rms = np.nan
    else:
        noise_rms = np.sqrt(np.mean(noise_vals.astype(float) ** 2))

    # Signal window
    signal_mask = (t_arr >= (start_time + snr_signal_start)) & (t_arr <= (start_time + snr_signal_end))
    sig_vals = signal_arr[signal_mask]
    sig_vals = sig_vals[~np.isnan(sig_vals)]

    if sig_vals.size == 0:
        signal_rms = np.nan
    else:
        signal_rms = np.sqrt(np.mean(sig_vals.astype(float) ** 2))

    # SNR #1: RMS-based
    if np.isnan(signal_rms) or np.isnan(noise_rms) or noise_rms == 0:
        snr_rms = np.nan
    else:
        snr_rms = float(signal_rms / noise_rms)

    # SNR #2: dynamic-range-based
    #   SNR_dynamic = (max(signal window) - mean(noise window)) / noise_rms
    if noise_vals.size == 0 or sig_vals.size == 0 or np.isnan(noise_rms) or noise_rms == 0:
        snr_dynamic = np.nan
    else:
        baseline_mean = float(np.mean(noise_vals))
        peak_signal   = float(np.max(sig_vals))
        dynamic_amp   = peak_signal - baseline_mean
        snr_dynamic   = dynamic_amp / noise_rms

    return {
        'detection_time_min': detection_time,   # absolute minutes
        'detection_index': detection_index,
        'signal_rms': signal_rms,
        'noise_rms': noise_rms,
        'snr_rms': snr_rms,
        'snr_dynamic': snr_dynamic,
        'rolling_short': rolling_short,
        'rolling_long': rolling_long
    }


def compute_snr_only(signal_arr, t_arr, start_time, led_label):
    """
    Compute SNR metrics ONLY (no detection, no rolling windows).
    Used for RAW signal.
    """
    # Noise window
    noise_mask = (t_arr >= (start_time + snr_noise_start)) & (t_arr <= (start_time + snr_noise_end))
    noise_vals = signal_arr[noise_mask]
    noise_vals = noise_vals[~np.isnan(noise_vals)]

    if noise_vals.size == 0:
        noise_rms = np.nan
    else:
        noise_rms = np.sqrt(np.mean(noise_vals.astype(float) ** 2))

    # Signal window
    signal_mask = (t_arr >= (start_time + snr_signal_start)) & (t_arr <= (start_time + snr_signal_end))
    sig_vals = signal_arr[signal_mask]
    sig_vals = sig_vals[~np.isnan(sig_vals)]

    if sig_vals.size == 0:
        signal_rms = np.nan
    else:
        signal_rms = np.sqrt(np.mean(sig_vals.astype(float) ** 2))

    # SNR #1: RMS-based
    if np.isnan(signal_rms) or np.isnan(noise_rms) or noise_rms == 0:
        snr_rms = np.nan
    else:
        snr_rms = float(signal_rms / noise_rms)

    # SNR #2: dynamic-range-based
    if noise_vals.size == 0 or sig_vals.size == 0 or np.isnan(noise_rms) or noise_rms == 0:
        snr_dynamic = np.nan
    else:
        baseline_mean = float(np.mean(noise_vals))
        peak_signal   = float(np.max(sig_vals))
        dynamic_amp   = peak_signal - baseline_mean
        snr_dynamic   = dynamic_amp / noise_rms

    return {
        'signal_rms': signal_rms,
        'noise_rms': noise_rms,
        'snr_rms': snr_rms,
        'snr_dynamic': snr_dynamic
    }

# --- FAM wells ---
for sub_df in fam_dfs_filtered:
    well = int(sub_df['Well'].iloc[0])

    # RAW signal
    signal_arr_raw = align_to_main_time(sub_df, signal_col='FAM/LED')

    # FILTERED signal for time call (FAM_filtered if present, else RAW)
    if 'FAM_filtered' in sub_df.columns:
        signal_arr_filt = align_to_main_time(sub_df, signal_col='FAM_filtered')
    else:
        print(f"Warning: 'FAM_filtered' column not found for well {well}. Using raw FAM/LED for detection.")
        signal_arr_filt = signal_arr_raw

    # Detection + SNR on FILTERED signal
    res_filt = compute_detection_and_snr(signal_arr_filt, time_main, start_65_time, 'FAM')

    # SNR on RAW signal
    res_raw = compute_snr_only(signal_arr_raw, time_main, start_65_time, 'FAM')

    # detection time relative to start_65_time (FILTERED)
    if np.isnan(res_filt['detection_time_min']):
        det_time_rel = np.nan
    else:
        det_time_rel = res_filt['detection_time_min'] - start_65_time

    # Summary row
    summary_rows.append({
        'Well': well,
        'LED': 'FAM',
        'Detection_Time_min_since_65': det_time_rel,
        'Detection_Index': res_filt['detection_index'],

        'Signal_RMS_raw': res_raw['signal_rms'],
        'Noise_RMS_raw':  res_raw['noise_rms'],
        'SNR_RMS_raw':    res_raw['snr_rms'],
        'SNR_dynamic_raw':res_raw['snr_dynamic'],

        'Signal_RMS_filt': res_filt['signal_rms'],
        'Noise_RMS_filt':  res_filt['noise_rms'],
        'SNR_RMS_filt':    res_filt['snr_rms'],
        'SNR_dynamic_filt':res_filt['snr_dynamic'],

        'Multiplier': multiplier['FAM']
    })

    # Wide rolling columns for this well (FILTERED signal)
    base = f'FAM_W{well}'
    rolling_wide_df[f'{base}_Signal']        = signal_arr_filt
    rolling_wide_df[f'{base}_Rolling_Short'] = res_filt['rolling_short']
    rolling_wide_df[f'{base}_Rolling_Long']  = res_filt['rolling_long']

    # --- PLOT for this well/LED (not saved) ---
    plt.figure()
    plt.plot(time_rel, signal_arr_filt, label='Signal (filtered)')
    plt.plot(time_rel, res_filt['rolling_short'], label=f'Rolling_Short ({short_window_min} min)')
    plt.plot(time_rel, res_filt['rolling_long'], label='Rolling_Long (-7 to -6 min)')

    # long * multiplier threshold (FILTERED baseline)
    fam_mult = multiplier['FAM']
    plt.plot(
        time_rel,
        res_filt['rolling_long'] * fam_mult,
        label=f'Rolling_Long × {fam_mult}'
    )

    # vertical line at detection time, if defined
    if not np.isnan(det_time_rel):
        plt.axvline(det_time_rel, linestyle='--', label='Positive Call')

    plt.xlabel('Time since 65°C start (min)')
    plt.ylabel('Fluorescence (a.u.)')
    plt.title(f'FAM Well {well}')
    plt.legend()
    plt.tight_layout()
    plt.show()

# --- TEX wells ---
for sub_df in tex_dfs_filtered:
    well = int(sub_df['Well'].iloc[0])

    # RAW signal
    signal_arr_raw = align_to_main_time(sub_df, signal_col='TEX/LED')

    # FILTERED signal for detection (TEX_filtered if present, else RAW)
    if 'TEX_filtered' in sub_df.columns:
        signal_arr_filt = align_to_main_time(sub_df, signal_col='TEX_filtered')
    else:
        print(f"Warning: 'TEX_filtered' column not found for well {well}. Using raw TEX/LED for detection.")
        signal_arr_filt = signal_arr_raw

    # Detection + SNR on FILTERED signal
    res_filt = compute_detection_and_snr(signal_arr_filt, time_main, start_65_time, 'TEX')

    # SNR on RAW signal
    res_raw = compute_snr_only(signal_arr_raw, time_main, start_65_time, 'TEX')

    # detection time relative to start_65_time (FILTERED)
    if np.isnan(res_filt['detection_time_min']):
        det_time_rel = np.nan
    else:
        det_time_rel = res_filt['detection_time_min'] - start_65_time

    # Summary row
    summary_rows.append({
        'Well': well,
        'LED': 'TEX',
        'Detection_Time_min_since_65': det_time_rel,
        'Detection_Index': res_filt['detection_index'],

        'Signal_RMS_raw': res_raw['signal_rms'],
        'Noise_RMS_raw':  res_raw['noise_rms'],
        'SNR_RMS_raw':    res_raw['snr_rms'],
        'SNR_dynamic_raw':res_raw['snr_dynamic'],

        'Signal_RMS_filt': res_filt['signal_rms'],
        'Noise_RMS_filt':  res_filt['noise_rms'],
        'SNR_RMS_filt':    res_filt['snr_rms'],
        'SNR_dynamic_filt':res_filt['snr_dynamic'],

        'Multiplier': multiplier['TEX']
    })

    # Wide rolling columns for this well (FILTERED signal)
    base = f'TEX_W{well}'
    rolling_wide_df[f'{base}_Signal']        = signal_arr_filt
    rolling_wide_df[f'{base}_Rolling_Short'] = res_filt['rolling_short']
    rolling_wide_df[f'{base}_Rolling_Long']  = res_filt['rolling_long']

    # --- PLOT for this well/LED (not saved) ---
    plt.figure()
    plt.plot(time_rel, signal_arr_filt, label='Signal (filtered)')
    plt.plot(time_rel, res_filt['rolling_short'], label=f'Rolling_Short ({short_window_min} min)')
    plt.plot(time_rel, res_filt['rolling_long'], label='Rolling_Long (-7 to -6 min)')

    # long * multiplier threshold
    tex_mult = multiplier['TEX']
    plt.plot(
        time_rel,
        res_filt['rolling_long'] * tex_mult,
        label=f'Rolling_Long × {tex_mult}'
    )

    if not np.isnan(det_time_rel):
        plt.axvline(det_time_rel, linestyle='--', label='Positive Call')

    plt.xlabel('Time since 65°C start (min)')
    plt.ylabel('Fluorescence (a.u.)')
    plt.title(f'TEX Well {well}')
    plt.legend()
    plt.tight_layout()
    plt.show()

# Save summary
summary_df = pd.DataFrame(summary_rows)
out_path = os.path.join(exp_dir, f"{today_date}_{exp_name}_rt_snr.csv")
summary_df.to_csv(out_path, index=False)
print(f"Saved real-time detection + SNR summary → {out_path}")

# Save wide rolling averages (FILTERED signal)
rolling_out_path = os.path.join(exp_dir, f"{today_date}_{exp_name}_rolling_avgs.csv")
rolling_wide_df.to_csv(rolling_out_path, index=False)
print(f"Saved rolling averages (wide, one column per well/metric) → {rolling_out_path}")

# Expose to globals for later inspection
globals()['rt_snr_summary_df'] = summary_df
globals()['rt_rolling_avgs_wide_df'] = rolling_wide_df

"""
Notes:
- Detection time and vertical line in plots are based on FILTERED signals
  (FAM_filtered / TEX_filtered where available; otherwise raw).
- SNR metrics are computed for BOTH raw and filtered signals and stored separately.
- Rolling averages and the wide CSV use the FILTERED signal.
"""
