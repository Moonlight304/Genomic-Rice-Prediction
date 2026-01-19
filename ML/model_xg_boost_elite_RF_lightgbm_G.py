import pandas as pd
from sklearn.model_selection import KFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.feature_selection import SelectFromModel
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'  # Using your G-only file
TARGET_VARIABLE = 'HDG_80HEAD' # Predicting Flowering Time
TOP_N_FEATURES = 1000 

print("--- Ensemble Prediction (XGB + RF + LightGBM) ---")
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

# --- 3. Prepare Data ---
print("\n[Status] Preparing data...")
y = df[TARGET_VARIABLE]

all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]
X = df.drop(columns=columns_to_drop)

X = pd.get_dummies(X, columns=['SUBPOPULATION'])
X = X.fillna(X.mean())

# --- 4. Feature Selection (Crucial for Speed) ---
# We use XGBoost to pick the best 1000 features first.
# If we fed all 4700 features to Random Forest, it would be very slow.
X_numpy = X.values 
y_numpy = y.values 

print(f"\n[Status] Selecting 'Top {TOP_N_FEATURES}' features to speed up the Ensemble...")
selector_model = XGBRegressor(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
selector_model.fit(X_numpy, y_numpy) 

selector = SelectFromModel(selector_model, max_features=TOP_N_FEATURES, threshold=-np.inf, prefit=True)
X_elite = selector.transform(X_numpy)

print(f"[Status] Feature selection complete. Data shape: {X_elite.shape}")

# --- 5. Define the 3 Models ---
print("\n[Status] Building the Ensemble Team...")

# Model 1: XGBoost (The Specialist)
xgb_model = XGBRegressor(
    n_estimators=300, max_depth=5, learning_rate=0.05, 
    subsample=0.8, colsample_bytree=0.8, n_jobs=-1, random_state=42
)

# Model 2: Random Forest (The Generalist)
rf_model = RandomForestRegressor(
    n_estimators=200, max_depth=15, 
    n_jobs=-1, random_state=42
)

# Model 3: LightGBM (The Speedster)
# Force verbosity to -1 to suppress warnings
lgbm_model = LGBMRegressor(
    n_estimators=300, learning_rate=0.05, num_leaves=31, 
    n_jobs=-1, random_state=42, verbose=-1
)

# --- 6. Create the Voting Ensemble ---
# This averages the predictions: (XGB + RF + LGBM) / 3
ensemble = VotingRegressor(
    estimators=[
        ('xgb', xgb_model), 
        ('rf', rf_model), 
        ('lgbm', lgbm_model)
    ],
    n_jobs=-1
)

# --- 7. Evaluate ---
print(f"[Status] Running 5-fold Cross-Validation on the Ensemble...")
cv = KFold(n_splits=5, shuffle=True, random_state=42)

# Note: We use X_elite (the top 1000 features)
scores = cross_val_score(ensemble, X_elite, y_numpy, cv=cv, scoring='r2', n_jobs=1)

print("\n" + "="*40)
print("--- ENSEMBLE RESULTS ---")
print(f"Individual Fold Scores: {[f'{s:.4f}' for s in scores]}")
print(f"MEAN R-SQUARED (R²): {scores.mean():.4f}")
print("="*40)

print(f"\n--- Script finished in {time.time() - start_time:.2f} seconds ---")