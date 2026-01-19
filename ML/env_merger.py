import pandas as pd
import numpy as np

# --- Configuration ---
ORIGINAL_FILE = 'GP_full.csv'
NEW_FILE = 'GEP_full.csv'
PHENOTYPE_COLUMN_COUNT = 12 # From our previous steps

print(f"Loading original file: {ORIGINAL_FILE}...")
try:
    df = pd.read_csv(ORIGINAL_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{ORIGINAL_FILE}' was not found.")
    exit()

print(f"Successfully loaded {df.shape[0]} samples.")

# --- Create New "Plausible" E-Data (as Integers) ---
print("Creating 10 plausible (but random) 'E' columns as integers...")
# Use a fixed random seed so the data is the same every time
np.random.seed(42) 
num_samples = len(df)

# Create a new DataFrame for the E-data
E_data = pd.DataFrame(
    {
        # --- MODIFICATION: Added .round().astype(int) to all lines ---
        'E_avg_temp': np.random.normal(27, 2, num_samples).round().astype(int),
        'E_max_temp': np.random.normal(33, 3, num_samples).round().astype(int),
        'E_total_rain_mm': np.random.normal(1200, 300, num_samples).round().astype(int),
        'E_soil_ph': np.random.normal(6.0, 0.5, num_samples).round().astype(int),
        'E_soil_nitrogen': np.random.normal(0.12, 0.05, num_samples).round().astype(int),
        'E_solar_radiation': np.random.normal(15, 3, num_samples).round().astype(int),
        'E_humidity_perc': np.random.normal(75, 8, num_samples).round().astype(int),
        'E_soil_moisture': np.random.normal(40, 10, num_samples).round().astype(int),
        'E_co2_ppm': np.random.normal(420, 20, num_samples).round().astype(int),
        'E_o2_perc': np.random.normal(20.9, 0.1, num_samples).round().astype(int)
    },
    index=df.index # Give it the same index as the main df
)

# --- Create and Save the New File ---
print(f"Joining genetic data with new 'E' data...")

# We know the order is: Sample_ID (1), SUBPOPULATION (1), Phenotypes (12)
# So, the split point is after column 1 + 1 + 12 = 14
SPLIT_INDEX = 1 + 1 + PHENOTYPE_COLUMN_COUNT

# Break the original dataframe into two parts
df_left = df.iloc[:, :SPLIT_INDEX]  # IDs, Subpop, Phenotypes
df_right = df.iloc[:, SPLIT_INDEX:] # Genotypes (SNPs)

# Concatenate in the correct order: [Left, New E_data, Right]
gep_df = pd.concat([df_left, E_data, df_right], axis=1)


print(f"Saving new dataset as '{NEW_FILE}'...")
# index=False keeps Sample_ID as a column
gep_df.to_csv(NEW_FILE, index=False) 

print("\n--- Done ---")
print(f"Successfully created {NEW_FILE} with shape: {gep_df.shape}")
print(f"All 10 'E' columns now contain only whole numbers.")