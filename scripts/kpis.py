import pandas as pd
import numpy as np

# Import data from DataFrames folder
stats = pd.read_csv("../DataFrames/NBA Player Stats and Salaries_2010-2025.csv")
phase_map = pd.read_csv("../DataFrames/nba_contract_phases.csv")

# Clean column headers and player name strings
phase_map.columns = phase_map.columns.str.strip()
stats.columns = stats.columns.str.strip()
phase_map['player'] = phase_map['player'].astype(str).str.strip()
stats['player'] = stats['player'].astype(str).str.strip()

# Combine data tables using an Inner Join
merged_df = pd.merge(phase_map, stats, on=['player', 'season'], how='inner')

# Force metrics to numeric to prevent data type crashes
numeric_fields = [
    'points', 'total_rebounds', 'assists', 'steals', 'blocks', 
    'fg_percentage', 'three_point_percentage', 'efg_percentage', 
    'minutes_played', 'turnovers', 'games'
]
for col in numeric_fields:
    if col in merged_df.columns:
        merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0.0)


# Formulate the KPIs
print("Formulating multi-dimensional performance KPIs...")
merged_df['efficient_scoring_value'] = merged_df['points'] * merged_df['efg_percentage']
merged_df['hustle_factor'] = (merged_df['total_rebounds'] + merged_df['steals'] + merged_df['blocks']) / (merged_df['minutes_played'] + 1e-6)
merged_df['offensive_creation_rate'] = merged_df['assists'] / (merged_df['turnovers'] + 0.1)
merged_df['availability_rate'] = merged_df['games'] / 82

merged_df['overall_impact_score'] = (
    merged_df['efficient_scoring_value'] + 
    (merged_df['hustle_factor'] * 100) + 
    (2 * merged_df['offensive_creation_rate']) + 
    (10 * merged_df['availability_rate'])
)

# Test contract phase mapping and KPI calculations
print("Engineering phase calculations on the career timeline...")

# Expanded to include all custom KPIs alongside traditional box score stats
metrics_to_test = [
    'points', 'total_rebounds', 'assists', 'steals', 'blocks', 
    'fg_percentage', 'three_point_percentage',
    'efficient_scoring_value', 'hustle_factor', 'offensive_creation_rate', 'availability_rate', 'overall_impact_score'
]

processed_frames = []

for player, player_df in merged_df.groupby('player'):
    
    global_baseline = player_df[player_df['phase'].str.contains('Baseline Year', na=False)][metrics_to_test].mean()
    if global_baseline.isna().any():
        global_baseline = player_df[metrics_to_test].iloc[0]
        
    for event_id, event_df in player_df.groupby('contract_event_id'):
        event_df_mapped = event_df.copy()
        
        baseline_rows = event_df_mapped[event_df_mapped['phase'].str.contains('Baseline Year', na=False)]
        contract_rows = event_df_mapped[event_df_mapped['phase'].str.contains('Contract Year', na=False)]
        
        base_means = baseline_rows[metrics_to_test].mean() if not baseline_rows.empty else global_baseline
        contract_means = contract_rows[metrics_to_test].mean() if not contract_rows.empty else event_df_mapped[metrics_to_test].iloc[0]
        
        for metric in metrics_to_test:
            b_val = base_means[metric] + 1e-6
            c_val = contract_means[metric] + 1e-6
            
            # 1. Pct Change from Baseline (Only pin to 0.0 if it explicitly says 'Baseline')
            event_df_mapped[f'{metric}_pct_change_from_baseline'] = np.where(
                event_df_mapped['phase'].str.contains('Baseline', case=False, na=False),
                0.0,
                (event_df_mapped[metric] - b_val) / b_val
            )
            
            # 2. Pct Change from Contract Year (Pin to 0.0 ONLY if it contains 'Contract' but NOT 'Post')
            is_contract_peak = event_df_mapped['phase'].str.contains('Contract', case=False, na=False) & \
                               ~event_df_mapped['phase'].str.contains('Post', case=False, na=False)
                               
            event_df_mapped[f'{metric}_pct_change_from_contract_year'] = np.where(
                is_contract_peak,
                0.0,
                (event_df_mapped[metric] - c_val) / c_val
            )
            
            # Clean up infinite/missing values
            for suffix in ['_pct_change_from_baseline', '_pct_change_from_contract_year']:
                event_df_mapped[f'{metric}{suffix}'] = event_df_mapped[f'{metric}{suffix}'].replace([np.inf, -np.inf], np.nan).fillna(0.0)
        processed_frames.append(event_df_mapped)

final_processed_df = pd.concat(processed_frames).sort_values(by=['player', 'season']).reset_index(drop=True)
final_processed_df = final_processed_df.round(3)


# Export the new dataset for Tableau visualization
print("Structuring final column mapping arrays for visualization...")

final_columns = [
    'player', 'position', 'season', 'phase', 'contract_event_id',
    
    # Percentage changes from baseline (Contract Year Spike analysis)
    'points_pct_change_from_baseline', 'total_rebounds_pct_change_from_baseline', 
    'assists_pct_change_from_baseline', 'steals_pct_change_from_baseline', 
    'blocks_pct_change_from_baseline', 'fg_percentage_pct_change_from_baseline', 
    'three_point_percentage_pct_change_from_baseline',
    'efficient_scoring_value_pct_change_from_baseline', 'hustle_factor_pct_change_from_baseline', 
    'offensive_creation_rate_pct_change_from_baseline', 'availability_rate_pct_change_from_baseline', 
    'overall_impact_score_pct_change_from_baseline',
    
    # Percentage changes from contract year (Post-Contract Hangover analysis)
    'points_pct_change_from_contract_year', 'total_rebounds_pct_change_from_contract_year', 
    'assists_pct_change_from_contract_year', 'steals_pct_change_from_contract_year', 
    'blocks_pct_change_from_contract_year', 'fg_percentage_pct_change_from_contract_year', 
    'three_point_percentage_pct_change_from_contract_year',
    'efficient_scoring_value_pct_change_from_contract_year', 'hustle_factor_pct_change_from_contract_year', 
    'offensive_creation_rate_pct_change_from_contract_year', 'availability_rate_pct_change_from_contract_year', 
    'overall_impact_score_pct_change_from_contract_year'
]

final_dashboard_df = final_processed_df[final_columns]
final_dashboard_df.to_csv("../DataFrames/nba_final_tableau_data.csv", index=False)
print(f"\nMaster data pipeline complete! Saved {len(final_dashboard_df)} rows tracking full box scores and custom KPIs.")