#%%
# Virtual environment venv
# python3 -m venv venv 
# source venv/bin/activate 
# pip install pandas ipykernel tk openpyxl matplotlib numpy seaborn

####### Running in the same interactive window as main
# settings - interactiveWindowMode - single

#%% Imports
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os
from io import StringIO
import matplotlib.pyplot as plt
import numpy as np

#%% Select file
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(
    title="Select the .txt file to analyze",
    filetypes=[("Text files", "*.txt")]
)

if not file_path:
    raise FileNotFoundError("No file selected.")

print(f"Selected file: {file_path}")

#%% Read file lines
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

#%% Find header line (ignore the timestamp column)
header_index = None
expected_column = "Bot_Resistor"  # unique column name from your header

for i, line in enumerate(lines):
    parts = line.strip().split('\t', 1)  # ignore first timestamp
    if len(parts) > 1 and expected_column in parts[1]:
        header_index = i
        break

if header_index is None:
    raise ValueError("No header line found containing expected columns.")

print(f"Header found at line: {header_index+1}")

#%% Create DataFrame from header onward
data_lines = lines[header_index:]
data_str = "".join(data_lines)
df = pd.read_csv(StringIO(data_str), sep='\t')

# print("DataFrame created successfully:")
# display(df.head())

#%%
# === Create Output Directory and Figure Dictionary ===
from datetime import datetime

# Define experiment name (optional: use filename)
# exp_name = os.path.splitext(os.path.basename(file_path))[0]

plt.rcParams.update({'font.size': 12})

# Create Output_Analysis directory next to input file
base_dir = os.path.dirname(file_path)
output_dir = os.path.join(base_dir, "Output_Analysis")
os.makedirs(output_dir, exist_ok=True)

# Create experiment-specific subdirectory inside Output_Analysis
today_date = datetime.today().strftime('%y%m%d')
exp_dir = os.path.join(output_dir, f"{today_date}_{exp_name}_graphs")
os.makedirs(exp_dir, exist_ok=True)

# Initialize a figure dictionary
fig_dict = {}

print(f"Experiment Name: {exp_name}")
print(f"Today's Date: {today_date}")
print(f"Output Directory: {exp_dir}")
# %%
