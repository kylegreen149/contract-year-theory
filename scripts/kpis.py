import pandas as pd
import numpy as np


# Read NBA Player Stats/Salaries file in DataFrames folder
stats_and_salaries = pd.read_csv("../DataFrames/NBA Player Stats and Salaries_2010-2025.csv")

# Filter to show only szns 2015-2025, & players who avg 12 min/game & 
    # 40 gms/szn to filter bench noise and injured players who may have skewed stats and salaries.
stats_and_salaries = stats_and_salaries[
    (stats_and_salaries['season'] >= 2015) & 
    (stats_and_salaries['season'] <= 2025) & 
    (stats_and_salaries["games"] >= 40) &
    (stats_and_salaries['minutes_played'] >= 12)]

print(stats_and_salaries.head())