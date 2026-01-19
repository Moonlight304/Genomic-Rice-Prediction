import pandas as pd
from catboost import CatBoostRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_absolute_error
import numpy as np
import time

# ==========================================
# --- 1. EXPERIMENT CONFIGURATION ---
# ==========================================
DATASET_FILE = 'GP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'

# Experiment Settings
TOP_N_FEATURES = 1000   
CV_FOLDS = 5            

# Model Settings (Tweak these!)
CAT_PARAMS = {'depth': 4, 'learning_rate': 0.1, 'iterations': 300, 'verbose': 0}
XGB_PARAMS = {'n_estimators': 300, 'max_depth': 5, 'learning_rate': 0.05}
LGB_PARAMS = {'n_estimators': 300, 'learning_rate': 0.05, 'num_leaves': 31, 'verbose': -1}

print("--- Model Battle: CatBoost vs XGBoost vs LightGBM (Manual Loop) ---")
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

# --- 4. The Battle (Manual Cross-Validation) ---
print(f"\n[Status] Running {CV_FOLDS}-Fold Cross-Validation manually...")

# Define the contenders
models = {
    "CatBoost": CatBoostRegressor(**CAT_PARAMS, random_state=42, allow_writing_files=False),
    "XGBoost ": XGBRegressor(**XGB_PARAMS, n_jobs=-1, random_state=42),
    "LightGBM": LGBMRegressor(**LGB_PARAMS, n_jobs=-1, random_state=42)
}

# Storage for scores
results = {name: {'r2': [], 'mae': []} for name in models.keys()}

kf = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=42)

# Loop through the data folds
fold_num = 1
for train_index, test_index in kf.split(X_elite):
    print(f"   Processing Fold {fold_num}/{CV_FOLDS}...")
    
    # Create the split
    X_train, X_test = X_elite[train_index], X_elite[test_index]
    y_train, y_test = y_numpy[train_index], y_numpy[test_index]
    
    # Train and Evaluate each model on THIS specific split
    for name, model in models.items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        
        # Calculate metrics
        r2 = r2_score(y_test, predictions)
        mae = mean_absolute_error(y_test, predictions)
        
        # Store them
        results[name]['r2'].append(r2)
        results[name]['mae'].append(mae)
        
    fold_num += 1

# --- 5. Final Report ---
print("\n" + "="*60)
print(f"{'MODEL':<10} | {'R² SCORE':<10} | {'MAE (Days)':<10} | {'STATUS'}")
print("="*60)

for name in models.keys():
    avg_r2 = np.mean(results[name]['r2'])
    avg_mae = np.mean(results[name]['mae'])
    print(f"{name:<10} | {avg_r2:.4f}     | {avg_mae:.2f}       | Done.")

print("="*60)
print(f"\n--- Experiment finished in {time.time() - start_time:.2f} seconds ---")