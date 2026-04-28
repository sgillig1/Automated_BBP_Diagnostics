#%% 6️⃣ Save Figures and Data
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Create directory if it doesn't exist
os.makedirs(exp_dir, exist_ok=True)

# Save each figure as PNG
for name, fig in fig_dict.items():
    fig.savefig(
        os.path.join(exp_dir, f"{today_date}_{exp_name}_{name}.png"),
        dpi=300,
        bbox_inches='tight'
    )

# Save the DataFrame as CSV
df.to_csv(os.path.join(exp_dir, f"{today_date}_{exp_name}_data.csv"), index=False)

# Save all figures in a multi-page PDF
pdf_path = os.path.join(exp_dir, f"{today_date}_{exp_name}_figures.pdf")
with PdfPages(pdf_path) as pdf:
    figs = list(fig_dict.values())
    num_figs = len(figs)
    figs_per_page = 4
    num_pages = (num_figs + figs_per_page - 1) // figs_per_page

    for page in range(num_pages):
        fig_page, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))  # A4 landscape
        axes = axes.flatten()

        for i in range(figs_per_page):
            fig_index = page * figs_per_page + i
            if fig_index < num_figs:
                canvas = FigureCanvas(figs[fig_index])
                canvas.draw()
                axes[i].imshow(canvas.buffer_rgba())
                axes[i].axis('off')
            else:
                axes[i].axis('off')

        plt.subplots_adjust(wspace=0.1, hspace=0.1)
        pdf.savefig(fig_page, bbox_inches='tight')
        plt.close(fig_page)
# %% Save Data for Prism Figures
# --- Save fluorescence export CSV ---
# Define time column (aligned to the main df_fluor)
time_main = df_fluor['Time_min'].reset_index(drop=True)
time_since_start65 = time_main - start_65_time

# Initialize export dataframe with desired column order
export_df = pd.DataFrame({
    'Time_since_Start65_min': time_since_start65,
    'Time_min': time_main
})

# Helper function to add columns for each well — removes outliers only, no interpolation
def add_fluorescence_columns(dfs_filtered, signal_col, prefix):
    for i, sub_df in enumerate(dfs_filtered):
        well = sub_df['Well'].iloc[0]
        label_raw = f'{prefix}_Well{well}_Raw'
        label_filtered = f'{prefix}_Well{well}_Filtered'

        # --- Process signal (no interpolation) ---
        y_raw = sub_df[signal_col].copy()
        y_clean = remove_outliers(y_raw)  # replaces outliers with NaN only
        y_smooth = y_clean.rolling(window=window, center=True, min_periods=1).mean()

        # --- Align to main time axis without interpolation ---
        y_raw_aligned = pd.Series(y_raw.values, index=sub_df['Time_min']).reindex(time_main)
        y_filt_aligned = pd.Series(y_smooth.values, index=sub_df['Time_min']).reindex(time_main)

        # --- Store in export_df ---
        export_df[label_raw] = y_raw_aligned.values
        export_df[label_filtered] = y_filt_aligned.values

# Add FAM and TEX fluorescence
add_fluorescence_columns(fam_dfs_filtered, 'FAM/LED', 'FAM')
add_fluorescence_columns(tex_dfs_filtered, 'TEX/LED', 'TEX')

# Save to CSV in the same directory
fluor_csv_path = os.path.join(exp_dir, f"{today_date}_{exp_name}_fluorescence.csv")
export_df.to_csv(fluor_csv_path, index=False)

print(f"✅ Saved fluorescence table to: {fluor_csv_path}")
print(f"✅ Saved data and figures in: {exp_dir}")
# %%
