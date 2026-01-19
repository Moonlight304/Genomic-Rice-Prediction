import pandas as pd
from sklearn.model_selection import KFold, RandomizedSearchCV
from xgboost import XGBRegressor
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GEP_full.csv' # <-- Load the new file with fake E
TARGET_VARIABLE = 'HDG_80HEAD'

print("--- P-from-(G+E+P) Model Experiment ---")
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

# --- *** THIS IS THE CHANGE *** ---
# We are *only* dropping the target variable.
# All other 11 phenotypes will now be kept as features.
columns_to_drop = [TARGET_VARIABLE]

# X will contain: Genetics (G) + Env (E) + 11 other Phenotypes (P)
X = df.drop(columns=columns_to_drop)
print(f"[Status] X now includes the 11 other phenotype traits.")
# --- *** END OF CHANGE *** ---

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
    n_jobs=-1 
)

# Using the *exact same* parameters that won our G-to-P test
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
    n_iter=1,  
    scoring='r2',
    cv=cv,
    n_jobs=1,  # Set to 1 to avoid the 'AttributeError'
    verbose=1,
    random_state=42
)

print("[Status] Starting the search (running sequentially)...")
search.fit(X, y)
print("[Status] Search complete.")

# --- 5. Report Model Performance ---
print("\n" + "="*40)
print("--- EXPERIMENT RESULTS (P-from-G+E+P) ---")
print(f"New R-squared (R²): {search.best_score_:.4f}")
print("="*40)
print(f"Previous G-only R-squared (R²): 0.6297")


end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")