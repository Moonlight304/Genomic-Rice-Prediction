import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import time

# --- 1. Configuration ---
ORIGINAL_FILE = 'GEP_full.csv'
NEW_FILE = 'GEP_pca.csv'
N_COMPONENTS = 0.95 # Keep components that explain 95% of the variance
PHENOTYPE_COUNT = 12
ENV_COUNT = 10

print(f"--- Creating PCA dataset from '{ORIGINAL_FILE}' ---")
start_time = time.time()

# --- 2. Load the Dataset ---
print(f"\n[Status] Loading dataset...")
try:
    df = pd.read_csv(ORIGINAL_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{ORIGINAL_FILE}' was not found.")
    exit()

print(f"[Status] Successfully loaded {df.shape[0]} samples.")

# --- 3. Separate the Data into Blocks ---
print("[Status] Separating data into blocks (Left, SNPs, Right)...")
# We know the order: ID(1), Subpop(1), Phenos(12), Env(10), SNPs(4694)
L_SPLIT = 1 + 1 + PHENOTYPE_COUNT
R_SPLIT = L_SPLIT + ENV_COUNT

df_left = df.iloc[:, :L_SPLIT]     # IDs, Subpop, Phenos
df_env = df.iloc[:, L_SPLIT:R_SPLIT]  # Environment columns
df_genos = df.iloc[:, R_SPLIT:]    # 4,694 SNPs

print(f"  Left block shape: {df_left.shape}")
print(f"  Env block shape: {df_env.shape}")
print(f"  Genotype block shape: {df_genos.shape}")

# --- 4. Prepare and Run PCA on Genotypes ---
print("\n[Status] Running PCA on Genotype block (4,694 SNPs)...")

# Step 4a: Impute missing values (must be done before scaling/PCA)
print("[Status] Imputing missing SNP values with mean...")
imputer = SimpleImputer(strategy='mean')
genos_imputed = imputer.fit_transform(df_genos)

# Step 4b: Scale the data (critical for PCA)
print("[Status] Scaling SNP data...")
scaler = StandardScaler()
genos_scaled = scaler.fit_transform(genos_imputed)

# Step 4c: Run PCA
print(f"[Status] Running PCA to capture {N_COMPONENTS*100}% of variance...")
pca = PCA(n_components=N_COMPONENTS, random_state=42)
genos_pca = pca.fit_transform(genos_scaled)

# Create a DataFrame for the new PCA components
pca_cols = [f'PC_{i+1}' for i in range(genos_pca.shape[1])]
df_pca = pd.DataFrame(genos_pca, columns=pca_cols)

print(f"[Status] PCA complete. {df_genos.shape[1]} SNPs compressed into {df_pca.shape[1]} Principal Components.")

# --- 5. Recombine and Save New File ---
print("\n[Status] Recombining all blocks...")
# One-hot encode subpopulation
df_left = pd.get_dummies(df_left, columns=['SUBPOPULATION'])

# Concatenate: [Left, Env, New PCA block]
df_final = pd.concat([df_left, df_env, df_pca], axis=1)

print(f"[Status] Saving new dataset as '{NEW_FILE}'...")
df_final.to_csv(NEW_FILE, index=False) 

print("\n--- Done ---")
print(f"Successfully created {NEW_FILE} with shape: {df_final.shape}")
end_time = time.time()
print(f"--- Script finished in {end_time - start_time:.2f} seconds ---")