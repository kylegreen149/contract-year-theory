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

# Initialize tracking columns directly to "Baseline Year 1"
stats_and_salaries['phase'] = 'Baseline Year 1'
stats_and_salaries['contract_event_id'] = 1.0

# --- PASS 1: MAP THE CONTRACT CRITICAL PEAKS ---
player_counts = {}
contract_event_indices = stats_and_salaries[stats_and_salaries['salary_growth_pct'].abs() >= 0.12].index

# Use .loc to select player per index
for idx in contract_event_indices:
    player = stats_and_salaries.loc[idx, 'player']
    
    if player not in player_counts:
        player_counts[player] = 1
    else:
        player_counts[player] += 1
        
    event_num = player_counts[player]
    
    # Tag Post-Contract Year
    stats_and_salaries.loc[idx, 'phase'] = f'Post-Contract Year {event_num}'
    stats_and_salaries.loc[idx, 'contract_event_id'] = float(event_num)
    
    # Tag Contract Year (One row above contract change, if same player)
    contract_idx = idx - 1
    if contract_idx >= 0 and stats_and_salaries.loc[contract_idx, 'player'] == player:
        stats_and_salaries.loc[contract_idx, 'phase'] = f'Contract Year {event_num}'
        stats_and_salaries.loc[contract_idx, 'contract_event_id'] = float(event_num)


# --- PASS 2: CHRONOLOGICAL BASELINE INCREMENTOR ---
# This steps forward through the data to update baseline numbers sequentially 
# once a player moves past their first or second contract events.
current_baseline_num = 1
current_event_id = 1.0

for i in range(len(stats_and_salaries)):
    # Reset tracking variables whenever switch to a brand new player happens
    if i == 0 or stats_and_salaries.loc[i, 'player'] != stats_and_salaries.loc[i-1, 'player']:
        current_baseline_num = 1
        current_event_id = 1.0
    
    phase_str = str(stats_and_salaries.loc[i, 'phase'])
    
    # If the row was caught by Pass 1 as a contract/post-contract year, 
    # update otracking numbers to match that event window
    if 'Contract' in phase_str:
        current_event_id = stats_and_salaries.loc[i, 'contract_event_id']
        # If they just finished a contract loop (Post-Contract Year), the NEXT baseline becomes event + 1
        if 'Post-Contract' in phase_str:
            current_baseline_num = int(current_event_id) + 1
    else:
        # If it's a normal unassigned year, assign it the active baseline version cleanly
        stats_and_salaries.loc[i, 'phase'] = f'Baseline Year {current_baseline_num}'
        stats_and_salaries.loc[i, 'contract_event_id'] = float(current_event_id)

# EXPORT CLEAN SEPARATE DESIGNATION MAP
output_columns = ['player', 'season', 'salary', 'salary_growth_pct', 'phase', 'contract_event_id']
stats_and_salaries_phase_map = stats_and_salaries[output_columns]

stats_and_salaries_phase_map.to_csv("../DataFrames/nba_contract_phases.csv", index=False)
print("Contract mapping engine execution complete! 'nba_contract_phases.csv' generated safely.")