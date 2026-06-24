import pandas as pd
import numpy as np

# Read CSV files
stats = pd.read_csv("../DataFrames/NBA Player Stats and Salaries_2010-2025.csv")
phase_map = pd.read_csv("../DataFrames/nba_contract_phases.csv")

# Clean column headers
phase_map.columns = phase_map.columns.str.strip()
stats.columns = stats.columns.str.strip()

# Clean the text strings inside the player columns
phase_map['player'] = phase_map['player'].astype(str).str.strip()
stats['player'] = stats['player'].astype(str).str.strip()

# Combine data tables using an Inner Join on key parameters
merged_df = pd.merge(phase_map, stats, on=['player', 'season'], how='inner')

# Sort chronologically to maintain career progression
merged_df = merged_df.sort_values(by=['player', 'season']).reset_index(drop=True)


# Clean all numeric columns immediately AFTER the merge so that 
#first set calculations don't throw type errors.
numeric_fields_to_clean = [
    'points', 'total_rebounds', 'assists', 'steals', 'blocks', 
    'fg_percentage', 'three_point_percentage', 'efg_percentage', 
    'minutes_played', 'turnovers', 'games'
]

for col in numeric_fields_to_clean:
    if col in merged_df.columns:
        merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0.0)

# Formulate custom KPIs

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

# FLAT BASELINE ENGINE & DIRECT CONTRACT YEAR COMPARISONS

tracked_metrics = [
    'points', 'total_rebounds', 'assists', 'steals', 'blocks', 
    'fg_percentage', 'three_point_percentage', 'overall_impact_score'
]

processed_frames = []

# Group by player to process careers independently
for player, player_df in merged_df.groupby('player'):
    
    # Store global baseline means for this player across their entire career 
    # to use as a fallback if a specific event id lacks a baseline row
    global_baseline = player_df[player_df['phase'].str.contains('Baseline Year', na=False)][tracked_metrics].mean()
    if global_baseline.isna().any():
        global_baseline = player_df[tracked_metrics].iloc[0] # ultimate fallback
        
    for event_id, event_df in player_df.groupby('contract_event_id'):
        event_df_mapped = event_df.copy()
        
        # 1. Identify baseline and contract rows for this specific event window
        baseline_rows = event_df_mapped[event_df_mapped['phase'].str.contains('Baseline Year', na=False)]
        contract_rows = event_df_mapped[event_df_mapped['phase'].str.contains('Contract Year', na=False)]
        
        # 2. Establish our anchors
        base_means = baseline_rows[tracked_metrics].mean() if not baseline_rows.empty else global_baseline
        contract_means = contract_rows[tracked_metrics].mean() if not contract_rows.empty else event_df_mapped[tracked_metrics].iloc[0]
        
        for metric in tracked_metrics:
            # --- CALCULATION 1: Vs Baseline (Baseline is locked to flat 0) ---
            b_val = base_means[metric] + 1e-6
            
            # If it's a baseline year row, force it to exactly 0.0
            event_df_mapped[f'{metric}_vs_baseline_pct'] = np.where(
                event_df_mapped['phase'].str.contains('Baseline Year', na=False),
                0.0,
                (event_df_mapped[metric] - b_val) / b_val
            )
            
            # --- CALCULATION 2: Vs Contract Year (Contract Year is locked to flat 0) ---
            c_val = contract_means[metric] + 1e-6
            event_df_mapped[f'{metric}_vs_contract_yr_pct'] = np.where(
                event_df_mapped['phase'].str.contains('Contract Year', na=False),
                0.0,
                (event_df_mapped[metric] - c_val) / c_val
            )
            
            # Clean up infinite values/NaN strings dynamically
            for suffix in ['_vs_baseline_pct', '_vs_contract_yr_pct']:
                event_df_mapped[f'{metric}{suffix}'] = event_df_mapped[f'{metric}{suffix}'].replace([np.inf, -np.inf], np.nan).fillna(0.0)
                
        processed_frames.append(event_df_mapped)

final_processed_df = pd.concat(processed_frames).sort_values(by=['player', 'season']).reset_index(drop=True)

# Round to 3 decimal places
final_processed_df = final_processed_df.round(3)

# Export Dataset

# Streamlined list: Only core metrics, custom KPIs, and percentage growth rows
tableau_columns = [
    # Core Dimensions
    'player', 'position', 'season', 'salary_x', 'salary_growth_pct', 'phase', 'contract_event_id',
    
    # Custom Formulated KPIs (Raw Values)
    'efficient_scoring_value', 'hustle_factor', 'offensive_creation_rate', 'availability_rate', 'overall_impact_score',
    
    # Baseline comparison metrics (% Shifts)
    'points_vs_baseline_pct', 'total_rebounds_vs_baseline_pct', 'assists_vs_baseline_pct', 
    'steals_vs_baseline_pct', 'blocks_vs_baseline_pct', 'fg_percentage_vs_baseline_pct', 
    'three_point_percentage_vs_baseline_pct', 'overall_impact_score_vs_baseline_pct',
    
    # Contract Year comparison metrics (% Shifts)
    'points_vs_contract_yr_pct', 'total_rebounds_vs_contract_yr_pct', 'assists_vs_contract_yr_pct', 
    'steals_vs_contract_yr_pct', 'blocks_vs_contract_yr_pct', 'fg_percentage_vs_contract_yr_pct', 
    'three_point_percentage_vs_contract_yr_pct', 'overall_impact_score_vs_contract_yr_pct'
]

# Extract destination dataset and normalize names
final_dashboard_df = final_processed_df[tableau_columns]
final_dashboard_df = final_dashboard_df.rename(columns={'salary_x': 'salary'})

# Save final clean master file
final_dashboard_df.to_csv("../DataFrames/nba_final_tableau_data.csv", index=False)
print(f"Master data pipeline complete! Saved {len(final_dashboard_df)} streamlined records into nba_final_tableau_data.csv.")