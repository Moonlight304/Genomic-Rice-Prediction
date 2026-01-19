import pandas as pd
from sklearn.model_selection import KFold, cross_val_score
from xgboost import XGBRegressor
from sklearn.feature_selection import SelectFromModel
import numpy as np
import time

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 1000 # <-- We will select the Top 1000 features

print("--- Genomic Prediction with Elite Feature Selection ---")
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

# --- 3. Prepare Data for Modeling (G-to-P) ---
print("\n[Status] Preparing data for modeling...")
y = df[TARGET_VARIABLE]

# Drop all phenotype columns
all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]
X = df.drop(columns=columns_to_drop)

print("[Status] One-hot encoding 'SUBPOPULATION' feature...")
X = pd.get_dummies(X, columns=['SUBPOPULATION'])

if X.isnull().sum().sum() > 0:
    print(f"[Status] {X.isnull().sum().sum()} missing values detected. Imputing with column mean...")
    X = X.fillna(X.mean())

print(f"[Status] Full feature matrix shape (X): {X.shape}")

# =========================================================================
# --- 4. ADVANCED STEP: Feature Selection (FIXED FOR VERSION COMPATIBILITY) ---
# =========================================================================

# **FIX:** Convert X to a NumPy array BEFORE feature selection to avoid the UserWarning
# This ensures SelectFromModel and XGBoost align by column index, not column names.
X_numpy = X.values 
y_numpy = y.values # Convert y as well for consistency

print(f"\n[Status] Selecting 'Top {TOP_N_FEATURES}' features from {X_numpy.shape[1]} total...")

# We use our best XGBoost model as the "judge"
selector_model = XGBRegressor(
    subsample=0.8, 
    n_estimators=300, 
    max_depth=5, 
    learning_rate=0.05, 
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

# Fit the judge on the pure NumPy array
selector_model.fit(X_numpy, y_numpy) 

# This object will select the features for us
selector = SelectFromModel(
    selector_model, 
    max_features=TOP_N_FEATURES, 
    threshold=-np.inf, 
    prefit=True
)

# Create the new, smaller "elite" dataset (this will also be a NumPy array)
X_elite = selector.transform(X_numpy)

# Get the names of the top features for our records (we use the original X columns)
elite_feature_names = X.columns[selector.get_support()]
print(f"[Status] 'X_elite' dataset created. Shape: {X_elite.shape}")
print(f"[Status] One of the top features: '{elite_feature_names[0]}'")

# --- 5. Evaluate the Model on "Elite" Features ---
print(f"\n[Status] Running 5-fold cross-validation on the 'Top {TOP_N_FEATURES}' features...")

# We use the *same model* again, but this time on the *elite data*
final_model = XGBRegressor(
    subsample=0.8, 
    n_estimators=300, 
    max_depth=5, 
    learning_rate=0.05, 
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

cv = KFold(n_splits=5, shuffle=True, random_state=42)

# We run the cross-validation on the new, smaller X_elite (the NumPy array)
scores = cross_val_score(final_model, X_elite, y_numpy, cv=cv, scoring='r2', n_jobs=1)

print("[Status] Model training complete.")

# --- 6. Report Final Results ---
print("\n" + "="*40)
print("--- FINAL 'FEATURE SELECTION' RESULTS ---")
print(f"R-squared scores from 5 folds: {[f'{s:.4f}' for s in scores]}")
print(f"Mean R-squared (R²) on 'Top {TOP_N_FEATURES}': {scores.mean():.4f}")
print("="*40)

end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")