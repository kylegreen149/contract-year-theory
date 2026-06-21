import pandas as pd
import numpy as np

# Read CSV file in DataFrames folder
stats_and_salaries = pd.read_csv("../DataFrames/NBA Player Stats and Salaries_2010-2025.csv")

# Filter to show only szns 2015-2025, & players who avg 12 min/game & 
    # 40 gms/szn to filter bench noise and injured players who may have skewed stats and salaries.
stats_and_salaries = stats_and_salaries[
    (stats_and_salaries['season'] >= 2015) & 
    (stats_and_salaries['season'] <= 2025) & 
    (stats_and_salaries["games"] >= 40) &
    (stats_and_salaries['minutes_played'] >= 12)]

# Sort chronologically by player and season
stats_and_salaries = stats_and_salaries.sort_values(by=['player', 'season']).reset_index(drop=True)

# Calculate salary growth relative to their own prior data row
stats_and_salaries['prev_salary'] = stats_and_salaries.groupby('player')['salary'].shift(1)
stats_and_salaries['salary_growth_pct'] = (stats_and_salaries['salary'] - stats_and_salaries['prev_salary']) / stats_and_salaries['prev_salary']

# Initialize target analysis tracking columns
stats_and_salaries['phase'] = 'Regular Year'
stats_and_salaries['contract_event_id'] = np.nan

# PLAYER-SCOPED MULTI-CONTRACT ALGORITHM
player_counts = {}

# Apply absolute value to capture changes >= 12% or <= -0.12 (salary increase or decrease of 12% or more)
contract_event_indices = stats_and_salaries[stats_and_salaries['salary_growth_pct'].abs() >= 0.12].index

for idx in contract_event_indices:
    player = stats_and_salaries.loc[idx, 'player']
    
    # Increment tracking count uniquely for this individual
    if player not in player_counts:
        player_counts[player] = 1
    else:
        player_counts[player] += 1
        
    event_num = player_counts[player]
    
    # Tag Post-Contract Year (The Change Year - Spike or Drop)
    stats_and_salaries.loc[idx, 'phase'] = f'Post-Contract Year {event_num}'
    stats_and_salaries.loc[idx, 'contract_event_id'] = event_num
    
    # Tag Contract Year (One row above contract change, if same player)
    contract_idx = idx - 1
    if contract_idx >= 0 and stats_and_salaries.loc[contract_idx, 'player'] == player:
        stats_and_salaries.loc[contract_idx, 'phase'] = f'Contract Year {event_num}'
        stats_and_salaries.loc[contract_idx, 'contract_event_id'] = event_num
        
        # Tag Baseline Years (Up to 3 rows above the contract year)
        for offset in range(1, 4):
            base_idx = contract_idx - offset
            if base_idx >= 0 and stats_and_salaries.loc[base_idx, 'player'] == player:
                # Shield existing contract boundaries from previous events
                if 'Year' not in str(stats_and_salaries.loc[base_idx, 'phase']):
                    stats_and_salaries.loc[base_idx, 'phase'] = f'Baseline Year {event_num}'
                    stats_and_salaries.loc[base_idx, 'contract_event_id'] = event_num

# EXPORT CLEAN SEPARATE DESIGNATION MAP
output_columns = ['player', 'season', 'salary', 'salary_growth_pct', 'phase', 'contract_event_id']
stats_and_salaries_phase_map = stats_and_salaries[output_columns]

stats_and_salaries_phase_map.to_csv("../DataFrames/nba_contract_phases.csv", index=False)
print("Contract mapping engine execution complete! 'nba_contract_phases.csv' generated safely.")