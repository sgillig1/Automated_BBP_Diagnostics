###### TO ADD: fluorescece X axis correct, baseline subtract

#%%
###### Select output .txt file and process into dataframe ######
#exec(open("1_Setup.py").read()) -- will have to change if I want to work in terminal to this
exp_name = "Device_v5.3"

%run -i "./1_Setup.py"

# Fixed colors for 4 wells
#colors = ['tab:red', 'tab:orange', 'tab:green', 'black']
colors = ['black', 'tab:blue', 'tab:green', 'tab:orange']
#colors = ['tab:green', 'tab:orange', 'black', 'tab:blue']

print("DataFrame created successfully:")
display(df.head())
# %%
###### Process Data and Split it out by wells ######
%run -i "./2_Data_Process.py"

print("Dataframe: ", df.head(1))               # Full DataFrame (all wells, all LED_Status, all columns)
print("Time: ", time[:5])                       # Time for wells where Well != 0 (NumPy array)
print("Temperature: ", temperature[:5])         # Temperature values corresponding to the above time points (NumPy array)
print("FAM DataFrame: ", fam_dfs[0].head(1))   # fam_dfs is a list of dataframes for each well (Well with LED_Status=1) (list of pandas DataFrame)
print("TEX DataFrame: ", tex_dfs[0].head(1))   # tex_dfs is a list of dataframes for each well (Well with LED_Status=2) (list of pandas DataFrame)
# %%
###### Timing Analysis - assess amplification relevant events ######
%run -i "./3_Timing.py"

print("Timing Analysis Results: ", time_tracking_df)
# %% Graphs for temperature and position
# A dictionary to store all generated figures.
# Key = descriptive name of the plot
# Value = the matplotlib figure object
# This allows easy saving/exporting of all figures later, e.g.:
# for name, fig in fig_dict.items():
#     fig.savefig(os.path.join(output_dir, f"{name}.png"), dpi=300)

%run -i "./4_temperature_position_graphs.py"

# %% 
####### Fluorescence Graphs - raw and filtered ######

%run -i "./5_Fluorescence.py"

# %%
####### Save all figures and data ######
%run -i "./6_Liftoff_Time.py"

# %%
####### Save all figures and data ######
%run -i "./7_Save.py"


# %%
