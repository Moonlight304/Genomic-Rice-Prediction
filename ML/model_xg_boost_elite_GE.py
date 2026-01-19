import pandas as pd
from sklearn.model_selection import KFold, RandomizedSearchCV
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
from sklearn.feature_selection import SelectFromModel
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GEP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 1000 

print("--- Final Tuning Experiment (XGBoost on G+E Elite Features) ---")
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

# --- 3. Prepare Full Data (G+E -> P) ---
print("\n[Status] Preparing full data for feature selection...")
y = df[TARGET_VARIABLE]

# Get *all* phenotype columns to drop
all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]

# X will contain: Genetics (G) + Env (E)
X = df.drop(columns=columns_to_drop) 
print(f"[Status] X now includes genetic data and 10 fake E-cols.")

print("[Status] One-hot encoding 'SUBPOPULATION' feature...")
X = pd.get_dummies(X, columns=['SUBPOPULATION'])

if X.isnull().sum().sum() > 0:
    print(f"[Status] {X.isnull().sum().sum()} missing values detected. Imputing with column mean...")
    X = X.fillna(X.mean())

print(f"[Status] Full feature matrix shape (X): {X.shape}") 

# =========================================================================
# --- 4. ADVANCED STEP: Feature Selection (FIXED) ---
# =========================================================================

# **FIX:** Convert X to a NumPy array to silence the version warning
X_numpy = X.values 
y_numpy = y.values

print(f"\n[Status] Selecting 'Top {TOP_N_FEATURES}' features from all {X_numpy.shape[1]}...")

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

# Train judge on NumPy array
selector_model.fit(X_numpy, y_numpy) 

# This object will select the features for us
selector = SelectFromModel(
    selector_model, 
    max_features=TOP_N_FEATURES, 
    threshold=-np.inf, # Ensures we get exactly TOP_N_FEATURES
    prefit=True 
)

# Transform the NumPy array
X_elite = selector.transform(X_numpy)

print(f"[Status] 'X_elite' dataset created. Shape: {X_elite.shape}")

# --- 5. Re-Tune XGBoost on "Elite" Features ---
print("\n[Status] Setting up new Hyperparameter Search on 'X_elite'...")

# Base model for the new search
base_model = XGBRegressor(
    # device='cuda',  # Use the GPU if available
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
    n_jobs=1, 
    verbose=1,  
    random_state=42
)

print("[Status] Starting the new search (this may take several minutes)...")
# We fit the new search on the ELITE NumPy data
random_search.fit(X_elite, y_numpy)
print("[Status] Search complete.")

# --- 6. Report Final Results ---
print("\n" + "="*40)
print("--- FINAL 'G + E' TUNING RESULTS ---")
print(f"Best R-squared (R²) found: {random_search.best_score_:.4f}")
print("\nBest Parameters Found:")
print(random_search.best_params_)
print("="*40)
print(f"Previous Best (G-only, Elite Features): 0.6623")

end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")