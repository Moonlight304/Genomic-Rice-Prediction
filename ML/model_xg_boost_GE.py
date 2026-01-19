import pandas as pd
from sklearn.model_selection import KFold, RandomizedSearchCV
from xgboost import XGBRegressor
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GEP_full.csv' # <-- Load the new file
TARGET_VARIABLE = 'HDG_80HEAD'

print("--- G(P) + E (Random Noise) Model Experiment ---")
start_time = time.time()

# --- 2. Load the Dataset ---
print(f"\n[Status] Loading dataset from '{DATASET_FILE}'...")
try:
    df = pd.read_csv(DATASET_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{DATASET_FILE}' was not found.")
    exit()

# Set the 'Sample_ID' column as the index for modeling
df.set_index(df.columns[0], inplace=True)
print(f"[Status] Successfully loaded dataset with {df.shape[0]} samples.")

# --- 3. Prepare Data for Modeling ---
print("\n[Status] Preparing data from new file for modeling...")
y = df[TARGET_VARIABLE]

# Get *all* phenotype columns to drop
all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]

# X will contain: Genetics (G) + *new* Env (E)
X = df.drop(columns=columns_to_drop)

print("[Status] One-hot encoding 'SUBPOPULATION' feature...")
X = pd.get_dummies(X, columns=['SUBPOPULATION'])

# Impute any missing SNP data
if X.isnull().sum().sum() > 0:
    print(f"[Status] {X.isnull().sum().sum()} missing values detected. Imputing with column mean...")
    X = X.fillna(X.mean())

print(f"[Status] Final feature matrix shape (X) now: {X.shape}")

# --- 4. Hyperparameter Tuning (Using our previous best settings) ---
print("\n[Status] Setting up XGBoost with previously found best parameters...")

base_model = XGBRegressor(
    # device='cuda',  # Uncomment this line in Google Colab!
    random_state=42,
    n_jobs=-1 # This n_jobs for the *model itself* is fine
)

# Using the *exact same* parameters that won our last test
param_grid = {
    'subsample': [0.8], 
    'n_estimators': [300], 
    'max_depth': [5], 
    'learning_rate': [0.05], 
    'colsample_bytree': [0.8]
}

cv = KFold(n_splits=5, shuffle=True, random_state=42)

search = RandomizedSearchCV(
    estimator=base_model,
    param_distributions=param_grid,
    n_iter=1,  # We only have 1 combination to test
    scoring='r2',
    cv=cv,
    # --- THIS IS THE FIX ---
    # Run sequentially (slower, but avoids the cleanup bug)
    n_jobs=1,  
    # --- END OF FIX ---
    verbose=1,
    random_state=42
)

print("[Status] Starting the search (running sequentially)...")
search.fit(X, y)
print("[Status] Search complete.")

# --- 5. Report Model Performance ---
print("\n" + "="*40)
print("--- EXPERIMENT RESULTS ---")
print(f"G+E+P R-squared (R²): {search.best_score_:.4f}")
print("="*40)

end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")