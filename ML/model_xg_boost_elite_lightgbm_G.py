import pandas as pd
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import KFold, cross_val_score
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 1000 

print("--- The Final Duel: XGBoost + LightGBM Ensemble ---")
start_time = time.time()

# --- 2. Load and Prepare Data ---
print(f"\n[Status] Loading dataset...")
df = pd.read_csv(DATASET_FILE)
df.set_index(df.columns[0], inplace=True)

y = df[TARGET_VARIABLE]
pheno_cols = ['CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
              'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT']
X = df.drop(columns=[c for c in pheno_cols if c in df.columns])
X = pd.get_dummies(X, columns=['SUBPOPULATION'])
X = X.fillna(X.mean())

X_numpy = X.values 
y_numpy = y.values 

# --- 3. Feature Selection ---
print(f"[Status] Selecting Top {TOP_N_FEATURES} Features (using XGBoost)...")
selector_model = XGBRegressor(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
selector_model.fit(X_numpy, y_numpy)
selector = SelectFromModel(selector_model, max_features=TOP_N_FEATURES, threshold=-np.inf, prefit=True)

X_elite = selector.transform(X_numpy)
print(f"[Status] Feature selection complete. Shape: {X_elite.shape}")

# --- 4. The Ensemble ---
print(f"\n[Status] Building and Validating Ensemble...")

# Champion 1: XGBoost (Using your winning settings)
xgb_model = XGBRegressor(
    n_estimators=300, 
    max_depth=5, 
    learning_rate=0.05, 
    n_jobs=-1, 
    random_state=42
)

# Champion 2: LightGBM
lgbm_model = LGBMRegressor(
    n_estimators=300, 
    learning_rate=0.05, 
    num_leaves=31, 
    n_jobs=-1, 
    random_state=42, 
    verbose=-1
)

# Voting Regressor: (XGBoost + LightGBM) / 2
ensemble = VotingRegressor(
    estimators=[('xgb', xgb_model), ('lgbm', lgbm_model)],
    n_jobs=-1
)

# --- 5. Validation ---
cv = KFold(n_splits=5, shuffle=True, random_state=42)
scores_r2 = cross_val_score(ensemble, X_elite, y_numpy, cv=cv, scoring='r2', n_jobs=1)
scores_mae = cross_val_score(ensemble, X_elite, y_numpy, cv=cv, scoring='neg_mean_absolute_error', n_jobs=1)

print("\n" + "="*40)
print("--- FINAL ENSEMBLE RESULTS ---")
print(f"Mean R² Score:        {scores_r2.mean():.4f} (Target: > 0.6707)")
print(f"Mean MAE (Days):      {-scores_mae.mean():.2f}")
print("="*40)

print(f"\n--- Script finished in {time.time() - start_time:.2f} seconds ---")