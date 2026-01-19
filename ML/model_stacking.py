import pandas as pd
from sklearn.model_selection import KFold, cross_val_score, cross_val_predict
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
from sklearn.linear_model import RidgeCV, LinearRegression
from sklearn.ensemble import StackingRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
import numpy as np
import time
import matplotlib.pyplot as plt

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 1000 # We will try to find the "Top 1000" features

print("--- Genomic Prediction with Elite Features + Stacking ---")
print(f"   (Comparing to Tuned XGBoost R^2: 0.6297)")
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

# --- 3. Prepare Data for Modeling (Identical to before) ---
print("\n[Status] Preparing data for modeling...")
y = df[TARGET_VARIABLE]

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
else:
    print("[Status] No missing values found in features.")

print(f"[Status] Full feature matrix shape (X): {X.shape}")

# --- 4. ADVANCED STEP 1: DEFINE "ELITE FEATURE" SELECTOR ---
print(f"\n[Status] Setting up 'Top {TOP_N_FEATURES}' Feature Selector...")

# We'll use the XGBoost model that won (R^2 0.63) as the "judge"
# We must use a version that *doesn't* use the GPU, as this part
# needs to be compatible with the scikit-learn pipeline.
feature_selector_model = XGBRegressor(
    subsample=0.8, 
    n_estimators=300, 
    max_depth=5, 
    learning_rate=0.05, 
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

# This will train the model and select only the top features
feature_selector = SelectFromModel(
    feature_selector_model, 
    max_features=TOP_N_FEATURES, 
    threshold=-np.inf # Ensure we get *exactly* TOP_N_FEATURES
)

# --- 5. ADVANCED STEP 2: DEFINE STACKING ENSEMBLE ---
print("[Status] Setting up Stacking Regressor...")

# These are the "base" models. They will be trained on the elite features.
estimators = [
    ('ridge', RidgeCV(alphas=np.logspace(-2, 4, 10))),
    ('xgb', XGBRegressor(
        subsample=0.8, 
        n_estimators=300, 
        max_depth=5, 
        learning_rate=0.05, 
        colsample_bytree=0.8,
        # device='cuda', # Uncomment in Colab
        random_state=42,
        n_jobs=-1
    ))
]

# The "meta-model" that learns from the base models' predictions
# A simple LinearRegression is the standard, most robust choice
stacking_model = StackingRegressor(
    estimators=estimators,
    final_estimator=LinearRegression(),
    cv=5, # The stacking model does its own internal cross-val
    n_jobs=-1
)

# --- 6. CREATE THE FINAL PIPELINE ---
# This pipeline does both steps automatically:
# 1. 'select_features': Run the feature selector to get Top 1000
# 2. 'stacking': Run the Stacking Model on those 1000 features
final_pipeline = Pipeline([
    ('select_features', feature_selector),
    ('stacking', stacking_model)
])

# --- 7. Train and Evaluate the Final Pipeline ---
print("\n[Status] Starting 5-fold cross-validation of the *entire* pipeline...")
print("(This will take a long time, as it's training 2 models + feature selection, 5 times)...")

cv = KFold(n_splits=5, shuffle=True, random_state=42)

scores = cross_val_score(final_pipeline, X, y, cv=cv, scoring='r2')

print("[Status] Model training complete.")

# --- 8. Report Final Results ---
print("\n" + "="*40)
print("--- FINAL 'DO WHATEVER' RESULTS ---")
print(f"R-squared scores from 5 folds: {[f'{s:.4f}' for s in scores]}")
print(f"Mean R-squared (R²): {scores.mean():.4f}")
print("="*40)
print(f"Previous Best (Tuned XGBoost): 0.6297")


end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")