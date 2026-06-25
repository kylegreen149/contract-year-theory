import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Create an output directory for your presentation slides if it doesn't exist
os.makedirs("presentation_charts", exist_ok=True)

# Load the granular dataset
df = pd.read_csv("../DataFrames/nba_final_tableau_data.csv")
df.columns = df.columns.str.strip()

# =====================================================================
# PART 1: HYPOTHESIS VALIDATION MATRIX (SUPPORT VS DISPROVE)
# =====================================================================
hyp_results = []
for (player, event_id), cycle_df in df.groupby(['player', 'contract_event_id']):
    contract_row = cycle_df[cycle_df['phase'].str.contains('Contract', case=False, na=False) & 
                            ~cycle_df['phase'].str.contains('Post', case=False, na=False)]
    post_row = cycle_df[cycle_df['phase'].str.contains('Post', case=False, na=False)]
    
    if contract_row.empty or post_row.empty:
        continue
        
    push_val = contract_row['overall_impact_score_pct_change_from_baseline'].iloc[0] * 100
    drop_val = post_row['overall_impact_score_pct_change_from_contract_year'].iloc[0] * 100
    position = contract_row['position'].iloc[0]
    
    supports = (push_val >= 10.0) and (drop_val <= -5.0)
    hyp_results.append({'player': player, 'position': position, 'push': push_val, 'drop': drop_val, 'supports': supports})

hyp_df = pd.DataFrame(hyp_results)

# Print Summary Results
total_cycles = len(hyp_df)
if total_cycles > 0:
    supported_cycles = hyp_df['supports'].sum()
    support_rate = (supported_cycles / total_cycles) * 100
    print("="*60)
    print("              HYPOTHESIS VALIDATION REPORT             ")
    print("="*60)
    print(f"Total Completed Contract Cycles Analyzed: {total_cycles}")
    print(f"Cycles supporting hypothesis: {supported_cycles} ({support_rate:.1f}%)")
    print("="*60)

# =====================================================================
# PART 2: LEAGUE-WIDE AGGREGATE TIMELINE GRAPH (FIGURE 1)
# =====================================================================
print("\nGenerating league-wide timeline chart...")
is_baseline = df['phase'].str.contains('Baseline', case=False, na=False)
is_contract = df['phase'].str.contains('Contract', case=False, na=False) & ~df['phase'].str.contains('Post', case=False, na=False)
is_post     = df['phase'].str.contains('Post', case=False, na=False)

avg_baseline = df[is_baseline]['overall_impact_score_pct_change_from_baseline'].mean() * 100
avg_contract = df[is_contract]['overall_impact_score_pct_change_from_baseline'].mean() * 100
avg_post     = df[is_post]['overall_impact_score_pct_change_from_baseline'].mean() * 100

plt.figure(1, figsize=(8, 5))  
bars = plt.bar(['Baseline Standard\n(Anchored at 0%)', 'Contract Year\n(The Push)', 'Post-Contract Year 1\n(The Hangover)'], 
               [avg_baseline, avg_contract, avg_post], color=['#3b82f6', '#10b981', '#ef4444'], width=0.5)

plt.axhline(0, color='black', linewidth=1)
plt.ylabel("Average Performance Shift vs. Baseline (%)", fontsize=11)
plt.title("League-Wide Performance Shift Across Contract Phases", fontsize=13, fontweight='bold', pad=15)
plt.grid(axis='y', linestyle='--', alpha=0.3)

for bar in bars:
    yval = bar.get_height()
    if pd.notna(yval) and np.isfinite(yval):
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + (0.5 if yval >= 0 else -1.5), f"{yval:+.2f}%", ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig("presentation_charts/0_league_wide_impact.png", dpi=300) 
print(" -> Saved: presentation_charts/0_league_wide_impact.png")


# =====================================================================
# PART 3: POSITION-SPECIFIC TARGETED DUAL KPI PROFILES (FIGURES 2-6)
# =====================================================================
print("Generating positional dual-phase charts...")

position_focus = {
    'C':  {'fig_num': 2, 'label': 'Centers', 'metrics': ['total_rebounds', 'blocks', 'hustle_factor']},
    'PF': {'fig_num': 3, 'label': 'Power Forwards', 'metrics': ['total_rebounds', 'blocks', 'hustle_factor']},
    'PG': {'fig_num': 4, 'label': 'Point Guards', 'metrics': ['assists', 'offensive_creation_rate', 'overall_impact_score']},
    'SG': {'fig_num': 5, 'label': 'Shooting Guards', 'metrics': ['points', 'efficient_scoring_value', 'overall_impact_score']},
    'SF': {'fig_num': 6, 'label': 'Small Forwards', 'metrics': ['points', 'efficient_scoring_value', 'overall_impact_score']}
}

for pos, config in position_focus.items():
    is_this_position = df['position'].str.contains(pos, case=False, na=False)
    
    # Isolate data frames for both phases separately
    pos_contract_data = df[is_this_position & is_contract].copy()
    pos_post_data = df[is_this_position & is_post].copy()
    
    if pos_contract_data.empty or pos_post_data.empty:
        print(f" -> Warning: Missing phase data for position: {pos}")
        continue
        
    # Construct metric target names built by kpis.py
    push_cols = [f"{m}_pct_change_from_baseline" for m in config['metrics']]
    drop_cols = [f"{m}_pct_change_from_contract_year" for m in config['metrics']]
    
    # Strip out math anomalies (>500% or <-500%) caused by tiny base values
    for col in push_cols:
        pos_contract_data[col] = pos_contract_data[col].mask(abs(pos_contract_data[col] * 100) > 500.0)
    for col in drop_cols:
        pos_post_data[col] = pos_post_data[col].mask(abs(pos_post_data[col] * 100) > 500.0)
        
    # Aggregate data
    avg_pushes = pos_contract_data[push_cols].mean() * 100
    avg_drops = pos_post_data[drop_cols].mean() * 100
    
    clean_metric_names = [m.replace('_', ' ').title() for m in config['metrics']]
    
    # Plot Side-by-Side Dual Bars
    plt.figure(config['fig_num'], figsize=(8, 5))
    x = np.arange(len(clean_metric_names))
    width = 0.35
    
    rects1 = plt.bar(x - width/2, avg_pushes, width, label='Contract Yr vs Baseline', color='#3b82f6')
    rects2 = plt.bar(x + width/2, avg_drops, width, label='Post-Contract Yr vs Contract Yr', color='#ef4444')
    
    plt.axhline(0, color='black', linewidth=0.8)
    plt.ylabel("Average Performance Shift (%)", fontsize=11)
    plt.title(f"Positional Contract Cycle: {config['label']}", fontsize=12, fontweight='bold', pad=12)
    plt.xticks(x, clean_metric_names)
    plt.legend(loc='best')
    plt.grid(axis='y', linestyle='--', alpha=0.3)
    
    # Text annotation helper for dual bars
    for rect in rects1:
        yval = rect.get_height()
        if pd.notna(yval) and np.isfinite(yval):
            plt.text(rect.get_x() + rect.get_width()/2.0, yval + (0.3 if yval >= 0 else -1.5), f"{yval:+.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold')
            
    for rect in rects2:
        yval = rect.get_height()
        if pd.notna(yval) and np.isfinite(yval):
            plt.text(rect.get_x() + rect.get_width()/2.0, yval + (0.3 if yval >= 0 else -1.5), f"{yval:+.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    plt.tight_layout()
    file_name = f"presentation_charts/{config['fig_num']}_{pos}_dual_contract_cycle.png"
    plt.savefig(file_name, dpi=300) 
    print(f" -> Saved: {file_name}")

print("\nAll side-by-side charts generated! Displaying interactive windows...")
# plt.show()