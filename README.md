# Automated_BBP_Diagnostics
Software for automation of instrument for automated detection of bloodborne pathogens. Developed as a part of the UW Lutz lab. Project in press for publication.

# Integrated Device Data Analysis & Control

## Overview
This repository contains scripts for operating an integrated diagnostic device and performing post-processing analysis of experimental data.

The workflow includes:
1. Device control and experiment execution (motor control, thermal cycling, amplification)
2. Data parsing and preprocessing
3. Timing and system performance analysis
4. Fluorescence signal processing (FAM/TEX)
5. Detection time and SNR calculations
6. Automated plotting and export of results

---

## Repository Structure

Integrated Device Manuscript Final Scripts/

├── Device Amplification Processing.py   # Master script to run full analysis pipeline  
├── 251013_Amplification_*.py            # ODrive device control + experiment execution  
├── 251023_Amplification_*.ino           # Microcontroller / firmware code  

├── Data Analysis Post-Processing/  
│   ├── 1_Setup.py                      # Load raw data and initialize environment  
│   ├── 2_Data_Process.py               # Clean and organize data by wells and channels  
│   ├── 3_Timing.py                    # Extract timing events (heating, amplification)  
│   ├── 4_temperature_position_graphs.py # Temperature + motion visualization  
│   ├── 5_Fluorescence.py              # Fluorescence processing + filtering + fitting  
│   ├── 6_Liftoff_Time.py              # Detection time + SNR analysis  
│   ├── 7_Save.py                      # Save figures and export data  

├── *.csv                              # Example output data  
└── venv/                              # Python virtual environment (optional)

---

## Workflow

### Run Full Pipeline
```bash
python Device\ Amplification\ Processing.py
```

### Or Run Step-by-Step
```python
%run -i 1_Setup.py
%run -i 2_Data_Process.py
%run -i 3_Timing.py
%run -i 4_temperature_position_graphs.py
%run -i 5_Fluorescence.py
%run -i 6_Liftoff_Time.py
%run -i 7_Save.py
```

---

## Step Descriptions

### 1_Setup.py
- Select raw .txt data file via GUI  
- Parses header and loads into a DataFrame  
- Initializes output directories  

### 2_Data_Process.py
- Converts timestamps to elapsed time (minutes)  
- Computes well position and deviation  
- Splits data into FAM and TEX channels  

### 3_Timing.py
- Identifies key experimental events:
  - Start of run  
  - Reach 50°C  
  - Reach 65°C  
- Computes timing intervals and exports CSV  

### 4_temperature_position_graphs.py
- Generates plots for:
  - Temperature profiles  
  - Heating behavior  
  - Position tracking  
  - System status  

### 5_Fluorescence.py
- Processes fluorescence signals:
  - Raw and filtered FAM/TEX  
  - Outlier removal  
  - Signal smoothing  
- Fits amplification curves (4-parameter logistic model)  

### 6_Liftoff_Time.py
- Computes detection time (real-time call)  
- Calculates SNR metrics  
- Outputs detection summary and rolling averages  

### 7_Save.py
- Saves:
  - Figures (PNG + PDF)  
  - Processed datasets  
  - Fluorescence tables  

---

## Outputs

Generated in:
Output_Analysis/<date>_<experiment>/

Includes:
- Figures (PNG + PDF)  
- Timing results CSV  
- Fluorescence data CSV  
- Detection + SNR summary  
- Rolling averages  

---

## Dependencies

Install required packages:

```bash
pip install pandas numpy matplotlib seaborn scipy tkinter openpyxl
```

---

## Notes
- Scripts rely on shared variables, so execution order matters  
- Designed for interactive use (Jupyter/IPython recommended)  
- Raw data must match expected column format  

---

## Context
This codebase supports development of an integrated molecular diagnostic system combining:
- Thermal control  
- Disk-based fluidics  
- Optical fluorescence detection  
- Automated data analysis  
