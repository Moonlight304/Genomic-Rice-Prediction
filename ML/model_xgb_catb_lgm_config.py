import pandas as pd
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.feature_selection import SelectFromModel
import joblib
import numpy as np
import time

# --- 1. Configuration (The Winner) ---
DATASET_FILE = 'GEP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 300
XGB_SHARE = 0.7
MODEL_FILENAME = 'models/rice_model_final.pkl'

print("--- Training the 0.7068 Grand Champion Model ---")
start_time = time.time()

# --- 2. Load Data ---
print(f"[Status] Loading dataset...")
df = pd.read_csv(DATASET_FILE)
df.set_index(df.columns[0], inplace=True)
y = df[TARGET_VARIABLE]

# Drop Phenotypes
pheno_cols = ['CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
              'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT']
X = df.drop(columns=[c for c in pheno_cols if c in df.columns])
X = pd.get_dummies(X, columns=['SUBPOPULATION'])
X = X.fillna(X.mean())

# Save statistics for the backend
training_means = X.mean()
training_columns = X.columns

X_numpy = X.values 
y_numpy = y.values 

# --- 3. Feature Selection (Top 500) ---
print(f"[Status] Selecting Top {TOP_N_FEATURES} Features...")
selector_model = XGBRegressor(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
selector_model.fit(X_numpy, y_numpy)
selector = SelectFromModel(selector_model, max_features=TOP_N_FEATURES, threshold=-np.inf, prefit=True)

X_elite = selector.transform(X_numpy)
print(f"[Status] Data filtered to shape: {X_elite.shape}")

# --- 4. Build Weighted Ensemble ---
print(f"[Status] Training Ensemble (70% XGBoost, 30% LightGBM)...")

xgb_model = XGBRegressor(
    n_estimators=300, 
    max_depth=5, 
    learning_rate=0.05, 
    n_jobs=-1, 
    random_state=42
)

lgbm_model = LGBMRegressor(
    n_estimators=300, 
    learning_rate=0.05, 
    num_leaves=31, 
    n_jobs=-1, 
    random_state=42, 
    verbose=-1
)

# We use the 'weights' parameter to enforce the 70/30 split
ensemble = VotingRegressor(
    estimators=[('xgb', xgb_model), ('lgbm', lgbm_model)],
    weights=[XGB_SHARE, 1 - XGB_SHARE],
    n_jobs=-1
)

ensemble.fit(X_elite, y_numpy)
print("[Status] Training complete.")

# --- 5. Save Everything ---
print(f"[Status] Saving to '{MODEL_FILENAME}'...")

production_package = {
    'model': ensemble,
    'selector': selector,
    'training_means': training_means,
    'training_columns': training_columns
}

joblib.dump(production_package, MODEL_FILENAME)
print(f"[Status] Model Saved. Ready for Backend.")

print(f"\n--- Script finished in {time.time() - start_time:.2f} seconds ---")