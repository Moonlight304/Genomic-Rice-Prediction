import pandas as pd
from sklearn.model_selection import KFold
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 1000 

print("--- CatBoost + LightGBM (Bulletproof Manual Mode) ---")
start_time = time.time()

# --- 2. Load the Dataset ---
print(f"\n[Status] Loading dataset from '{DATASET_FILE}'...")
try:
    df = pd.read_csv(DATASET_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{DATASET_FILE}' was not found.")
    exit()

df.set_index(df.columns[0], inplace=True)
y = df[TARGET_VARIABLE]
all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]
X = df.drop(columns=columns_to_drop)
X = pd.get_dummies(X, columns=['SUBPOPULATION'])
X = X.fillna(X.mean())

X_numpy = X.values 
y_numpy = y.values 

# --- 3. Feature Selection ---
print(f"\n[Status] Selecting 'Top {TOP_N_FEATURES}' features...")
selector_model = XGBRegressor(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
selector_model.fit(X_numpy, y_numpy) 
selector = SelectFromModel(selector_model, max_features=TOP_N_FEATURES, threshold=-np.inf, prefit=True)
X_elite = selector.transform(X_numpy)
print(f"[Status] Feature selection complete. Data shape: {X_elite.shape}")

# --- 4. MANUAL GRID SEARCH (No Scikit-Learn Wrappers) ---
print("\n[Status] Running Manual Grid Search on CatBoost...")

depths = [4, 6]
learning_rates = [0.05, 0.1]
iterations = [200, 300]

best_score = -np.inf
best_params = {}

# We do the looping ourselves to avoid the bug
kf_search = KFold(n_splits=3, shuffle=True, random_state=42)
total_combos = len(depths) * len(learning_rates) * len(iterations)
current_combo = 0

for d in depths:
    for lr in learning_rates:
        for it in iterations:
            current_combo += 1
            print(f"   > Testing Combo {current_combo}/{total_combos} (D={d}, LR={lr}, It={it})...", end="")
            
            fold_scores = []
            # Manual K-Fold Loop
            for train_idx, val_idx in kf_search.split(X_elite):
                X_train, X_val = X_elite[train_idx], X_elite[val_idx]
                y_train, y_val = y_numpy[train_idx], y_numpy[val_idx]
                
                model = CatBoostRegressor(
                    depth=d, learning_rate=lr, iterations=it,
                    verbose=0, random_state=42, allow_writing_files=False
                )
                model.fit(X_train, y_train)
                preds = model.predict(X_val)
                fold_scores.append(r2_score(y_val, preds))
            
            mean_score = np.mean(fold_scores)
            print(f" R²: {mean_score:.4f}")
            
            if mean_score > best_score:
                best_score = mean_score
                best_params = {'depth': d, 'learning_rate': lr, 'iterations': it}

print(f"\n   >>> WINNER: {best_params} with Score: {best_score:.4f}")

# --- 5. FINAL EVALUATION (Manual Ensemble) ---
print(f"\n[Status] Evaluating Final Ensemble with 5-fold CV...")
kf_final = KFold(n_splits=5, shuffle=True, random_state=42)

final_r2 = []
final_mae = []
final_rmse = []

for fold, (train_idx, val_idx) in enumerate(kf_final.split(X_elite)):
    X_train, X_val = X_elite[train_idx], X_elite[val_idx]
    y_train, y_val = y_numpy[train_idx], y_numpy[val_idx]
    
    # 1. Train Tuned CatBoost
    cat = CatBoostRegressor(
        depth=best_params['depth'], learning_rate=best_params['learning_rate'], 
        iterations=best_params['iterations'], verbose=0, random_state=42, allow_writing_files=False
    )
    cat.fit(X_train, y_train)
    pred_cat = cat.predict(X_val)
    
    # 2. Train LightGBM
    lgbm = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, n_jobs=-1, random_state=42, verbose=-1)
    lgbm.fit(X_train, y_train)
    pred_lgbm = lgbm.predict(X_val)
    
    # 3. Average Predictions (The Ensemble)
    pred_ensemble = (pred_cat + pred_lgbm) / 2
    
    # 4. Calculate Metrics
    r2 = r2_score(y_val, pred_ensemble)
    mae = mean_absolute_error(y_val, pred_ensemble)
    rmse = np.sqrt(mean_squared_error(y_val, pred_ensemble))
    
    final_r2.append(r2)
    final_mae.append(mae)
    final_rmse.append(rmse)
    print(f"   Fold {fold+1}: R²={r2:.4f}, MAE={mae:.2f}")

print("\n" + "="*40)
print("--- FINAL ENSEMBLE RESULTS ---")
print(f"R-Squared (Accuracy):  {np.mean(final_r2):.4f}")
print(f"MAE (Avg Days Error):  {np.mean(final_mae):.2f}")
print(f"RMSE (Large Errors):   {np.mean(final_rmse):.2f}")
print("="*40)

print(f"\n--- Script finished in {time.time() - start_time:.2f} seconds ---")