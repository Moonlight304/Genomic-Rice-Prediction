import pandas as pd
from sklearn.model_selection import KFold, RandomizedSearchCV
from xgboost import XGBRegressor
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GEP_pca.csv' # <-- Load the new PCA file
TARGET_VARIABLE = 'HDG_80HEAD'

print("--- P-from-(G+E+P) Model Experiment (with PCA) ---")
start_time = time.time()

# --- 2. Load the Dataset ---
print(f"\n[Status] Loading dataset from '{DATASET_FILE}'...")
try:
    df = pd.read_csv(DATASET_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{DATASET_FILE}' was not found.")
    exit()

df.set_index(df.columns[0], inplace=True)
print(f"[Status] Successfully loaded dataset with {df.shape[0]} samples.")

# --- 3. Prepare Data for Modeling ---
print("\n[Status] Preparing data from new file for modeling...")
y = df[TARGET_VARIABLE]

# We are *only* dropping the target variable.
columns_to_drop = [TARGET_VARIABLE]

# X will contain: 11 Phenos + Subpop_OHE + Env + PCA_Components
X = df.drop(columns=columns_to_drop)
print(f"[Status] X includes 11 phenos, E-cols, and new PCA features.")

# Note: Subpopulation is already one-hot encoded from the creation script
# Note: All missing data was handled in the creation script
print(f"[Status] Final feature matrix shape (X) now: {X.shape}")

# --- 4. Hyperparameter Tuning (Using our previous best settings) ---
print("\n[Status] Setting up XGBoost with previously found best parameters...")

base_model = XGBRegressor(
    # device='cuda',  # Uncomment this line in Google Colab!
    random_state=42,
    n_jobs=-1 
)

# Using the *exact same* parameters
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
print("--- EXPERIMENT RESULTS (PCA Model) ---")
print(f"NEW PCA-based R-squared (R²): {search.best_score_:.4f}")
print("="*40)
print(f"Previous SNP-based R-squared (R²): 0.6429")

end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")