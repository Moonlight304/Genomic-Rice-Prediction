import pandas as pd
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import KFold, cross_val_score
import numpy as np
import joblib
import time

# --- 1. Configuration ---
DATASET_FILE = 'GEP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 500 
MODEL_FILENAME = 'models/rice_model_GE.pkl'

print("--- The Final Duel: XGBoost + LightGBM (G + Fake E Data) ---")
start_time = time.time()

# --- 2. Load and Prepare Data ---
print(f"\n[Status] Loading dataset from '{DATASET_FILE}'...")
try:
    df = pd.read_csv(DATASET_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{DATASET_FILE}' was not found.")
    exit()

df.set_index(df.columns[0], inplace=True)
print(f"[Status] Successfully loaded dataset with {df.shape[0]} samples.")

y = df[TARGET_VARIABLE]

# Drop Phenotypes (P) so we are left with Genetics (G) + Environment (E)
pheno_cols = ['CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
              'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT']
columns_to_drop = [col for col in pheno_cols if col in df.columns]
X = df.drop(columns=columns_to_drop)

print("[Status] One-hot encoding 'SUBPOPULATION'...")
X = pd.get_dummies(X, columns=['SUBPOPULATION'])
X = X.fillna(X.mean())

# Save these for the backend later! (To handle new user data correctly)
training_means = X.mean()
training_columns = X.columns

# Convert to NumPy for the models
X_numpy = X.values 
y_numpy = y.values 

print(f"[Status] Feature Matrix Shape (G+E): {X.shape}") 

# --- 3. Feature Selection ---
print(f"\n[Status] Selecting Top {TOP_N_FEATURES} Features (using XGBoost)...")
selector_model = XGBRegressor(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
selector_model.fit(X_numpy, y_numpy)
selector = SelectFromModel(selector_model, max_features=TOP_N_FEATURES, threshold=-np.inf, prefit=True)

X_elite = selector.transform(X_numpy)
print(f"[Status] Feature selection complete. Shape: {X_elite.shape}")

# --- 4. The Ensemble Definition ---
print(f"\n[Status] Building and Validating Ensemble...")

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

ensemble = VotingRegressor(
    estimators=[('xgb', xgb_model), ('lgbm', lgbm_model)],
    n_jobs=-1
)

# --- 5. Validation (Just to double check score) ---
cv = KFold(n_splits=5, shuffle=True, random_state=42)
scores_r2 = cross_val_score(ensemble, X_elite, y_numpy, cv=cv, scoring='r2', n_jobs=1)
scores_mae = cross_val_score(ensemble, X_elite, y_numpy, cv=cv, scoring='neg_mean_absolute_error', n_jobs=1)

print("\n" + "="*40)
print("--- FINAL ENSEMBLE RESULTS (G+E) ---")
print(f"Mean R² Score:        {scores_r2.mean():.4f}")
print(f"Mean MAE (Days):      {-scores_mae.mean():.2f}")
print("="*40)

# ==========================================
# --- 6. PRODUCTION: Train & Save ---
# ==========================================
print(f"\n[Status] Retraining on 100% of data for Production...")

# We must refit on the full X_elite dataset
ensemble.fit(X_elite, y_numpy)

print(f"[Status] Saving production model to '{MODEL_FILENAME}'...")

# We bundle everything needed for the backend into one dictionary
production_package = {
    'model': ensemble,             # The trained XGB+LGBM
    'selector': selector,          # The logic to pick top 1000 features
    'training_means': training_means,   # Needed to impute missing user data
    'training_columns': training_columns # Needed to align user columns
}

joblib.dump(production_package, MODEL_FILENAME)
print(f"[Status] SUCCESS! Model saved. You can now use '{MODEL_FILENAME}' in your backend.")

print(f"\n--- Script finished in {time.time() - start_time:.2f} seconds ---")