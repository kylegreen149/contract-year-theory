import pandas as pd
import numpy as np

# Read NBA Player Stats/Salaries file in DataFrames folder
stats = pd.read_csv("../DataFrames/NBA Player Stats and Salaries_2010-2025.csv")

# print(stats.head())

# Read Contract Phases file in DataFrames folder
phase_map = pd.read_csv("../DataFrames/nba_contract_phases.csv")
# print(phase_map.head())

# Merge dataframes using an Inner Join
merged_df = pd.merge(phase_map, stats, on=['player', 'season'], how='inner')
print(merged_df.head())