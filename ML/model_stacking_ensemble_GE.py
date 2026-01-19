import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
import time

# --- 1. Configuration ---
DATASET_FILE = 'GEP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'

# We will test ALL these combinations
# FEATURE_COUNTS = [300, 350, 400, 450, 500]
# XGB_WEIGHTS    = [0.4, 0.5, 0.6, 0.7, 0.8]

FEATURE_COUNTS = [300]
XGB_WEIGHTS    = [0.7]

print("--- The Final Optimization: Feature Counts & Weighted Ensembles ---")
start_time = time.time()

# --- 2. Load Data ---
print(f"[Status] Loading dataset...")
df = pd.read_csv(DATASET_FILE)
df.set_index(df.columns[0], inplace=True)
y_raw = df[TARGET_VARIABLE]

pheno_cols = ['CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
              'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT']
X = df.drop(columns=[c for c in pheno_cols if c in df.columns])
X = pd.get_dummies(X, columns=['SUBPOPULATION'])
X = X.fillna(X.mean())

X_numpy = X.values 
y_numpy = y_raw.values

# --- 3. The Grand Loop ---
best_overall_score = -np.inf
best_config = {}

kf = KFold(n_splits=5, shuffle=True, random_state=42)

for n_features in FEATURE_COUNTS:
    print(f"\n[Testing] Top {n_features} Features...")
    
    # A. Feature Selection
    selector_model = XGBRegressor(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
    selector_model.fit(X_numpy, y_numpy)
    selector = SelectFromModel(selector_model, max_features=n_features, threshold=-np.inf, prefit=True)
    X_elite = selector.transform(X_numpy)
    
    # B. Cross Validation Loop
    fold_predictions = []
    fold_actuals = []
    
    # We collect ALL predictions first, then test weights
    # This saves time so we don't retrain models for every weight change
    for train_idx, val_idx in kf.split(X_elite):
        X_train, X_val = X_elite[train_idx], X_elite[val_idx]
        y_train, y_val = y_numpy[train_idx], y_numpy[val_idx]
        
        # Train XGB
        xgb = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, n_jobs=-1, random_state=42)
        xgb.fit(X_train, y_train)
        p_xgb = xgb.predict(X_val)
        
        # Train LGBM
        lgb = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, verbose=-1, n_jobs=-1, random_state=42)
        lgb.fit(X_train, y_train)
        p_lgb = lgb.predict(X_val)
        
        fold_predictions.append((p_xgb, p_lgb))
        fold_actuals.append(y_val)

    # C. Test Weights
    for w_xgb in XGB_WEIGHTS:
        w_lgb = 1.0 - w_xgb
        
        scores = []
        for i in range(5):
            p_xgb, p_lgb = fold_predictions[i]
            y_val = fold_actuals[i]
            
            # Weighted Average
            ensemble_pred = (p_xgb * w_xgb) + (p_lgb * w_lgb)
            scores.append(r2_score(y_val, ensemble_pred))
        
        avg_score = np.mean(scores)
        print(f"   > Weights (XGB:{w_xgb:.1f}, LGB:{w_lgb:.1f}) -> R²: {avg_score:.4f}")
        
        if avg_score > best_overall_score:
            best_overall_score = avg_score
            best_config = {
                'features': n_features,
                'xgb_weight': w_xgb,
                'lgb_weight': w_lgb
            }

print("\n" + "="*40)
print("--- 🏆 NEW CHAMPION SETTINGS ---")
print(f"Best R² Score:   {best_overall_score:.4f}")
print(f"Feature Count:   {best_config['features']}")
print(f"Ensemble Mix:    {best_config['xgb_weight']*100:.0f}% XGBoost + {best_config['lgb_weight']*100:.0f}% LightGBM")
print("="*40)

print(f"\n--- Script finished in {time.time() - start_time:.2f} seconds ---")