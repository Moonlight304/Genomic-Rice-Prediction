import pandas as pd
from sklearn.model_selection import KFold, RandomizedSearchCV
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
from sklearn.feature_selection import SelectFromModel
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GEP_full.csv' # <-- Using the G+E+P file
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 1000 # We will select the Top 1000 features

print("--- Final Tuning Experiment (XGBoost on G+E+P Elite Features) ---")
print(f"   (Comparing to G-only R^2: 0.6623)")
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

# --- 3. Prepare Full Data (G+E+P-to-P) ---
print("\n[Status] Preparing full data for feature selection...")
y = df[TARGET_VARIABLE]

# We are *only* dropping the target variable.
columns_to_drop = [TARGET_VARIABLE]

# X will contain: Genetics (G) + Env (E) + 11 other Phenotypes (P)
X = df.drop(columns=columns_to_drop)
print(f"[Status] X now includes 11 phenos, 10 E-cols, and genetic data.")

print("[Status] One-hot encoding 'SUBPOPULATION' feature...")
X = pd.get_dummies(X, columns=['SUBPOPULATION'])

if X.isnull().sum().sum() > 0:
    print(f"[Status] {X.isnull().sum().sum()} missing values detected. Imputing with column mean...")
    X = X.fillna(X.mean())

print(f"[Status] Full feature matrix shape (X): {X.shape}") # (1011, 4727)

# --- 4. Select the "Elite 1000" Features ---
print(f"\n[Status] Selecting 'Top {TOP_N_FEATURES}' features from all 4727...")

# We use a well-performing model as the "judge"
selector_model = XGBRegressor(
    subsample=0.8, 
    n_estimators=300, 
    max_depth=5, 
    learning_rate=0.05, 
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

selector_model.fit(X, y) # Train the judge on all features

# This object will select the features for us
selector = SelectFromModel(
    selector_model, 
    max_features=TOP_N_FEATURES, 
    threshold=-np.inf, # Ensures we get exactly TOP_N_FEATURES
    prefit=True # We already fitted the model
)

# Create the new, smaller "elite" dataset
X_elite = selector.transform(X)

print(f"[Status] 'X_elite' dataset created. Shape: {X_elite.shape}")

# --- 5. Re-Tune XGBoost on "Elite" Features ---
print("\n[Status] Setting up new Hyperparameter Search on 'X_elite'...")

# Base model for the new search
base_model = XGBRegressor(
    # device='cuda',  # Use the GPU! (Remove if on local CPU)
    random_state=42,
    n_jobs=-1
)

# Define a NEW, wider grid of parameters to try
param_grid = {
    'n_estimators': [200, 300, 400],           # Number of trees
    'learning_rate': [0.01, 0.05, 0.1],        # Speed of learning
    'max_depth': [3, 5, 7, 9],                 # Try deeper trees
    'colsample_bytree': [0.7, 0.8, 0.9],       # % of features per tree
    'subsample': [0.7, 0.8, 0.9]               # % of samples per tree
}

cv = KFold(n_splits=5, shuffle=True, random_state=42)

# Set up the Randomized Search
random_search = RandomizedSearchCV(
    estimator=base_model,
    param_distributions=param_grid,
    n_iter=20,  # Try 20 different combinations
    scoring='r2',
    cv=cv,
    n_jobs=-1,
    verbose=1,  # Show progress
    random_state=42
)

print("[Status] Starting the new search (this may take several minutes)...")
# We fit the new search on the ELITE data
random_search.fit(X_elite, y)
print("[Status] Search complete.")

# --- 6. Report Final Results ---
print("\n" + "="*40)
print("--- FINAL 'GEP' TUNING RESULTS ---")
print(f"Best R-squared (R²) found: {random_search.best_score_:.4f}")
print("\nBest Parameters Found:")
print(random_search.best_params_)
print("="*40)
print(f"Previous Best (G-only, Elite Features): 0.6623")
print(f"Previous Best (G-only, All Features):   0.6297")

end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")