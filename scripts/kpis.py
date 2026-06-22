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

# Formulate KPI'S

#KPI 1: ESV
merged_df['efficient_scoring_value'] = merged_df['points'] * merged_df['efg_percentage']

# KPI 2: HF
# 1e-6 cushion protects against accidental division-by-zero errors
merged_df['hustle_factor'] = (
    merged_df['total_rebounds'] + merged_df['steals'] + merged_df['blocks']
) / (merged_df['minutes_played'] + 1e-6)

# KPI 3: OCR
# 0.1 cushion added to denominator to prevent division-by-zero errors for players with zero turnovers
merged_df['offensive_creation_rate'] = merged_df['assists'] / (merged_df['turnovers'] + 0.1)

# KPI 4: AR
merged_df['availability_rate'] = merged_df['games'] / 82

# KPI 5: OIS (Master KPI)
merged_df['overall_impact_score'] = (
    merged_df['efficient_scoring_value'] + 
    (merged_df['hustle_factor'] * 100) + 
    (2 * merged_df['offensive_creation_rate']) + 
    (10 * merged_df['availability_rate'])
)

print(merged_df.head(50))