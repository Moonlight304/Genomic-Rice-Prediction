import pandas as pd
from sklearn.model_selection import KFold, cross_val_score, cross_val_predict
from sklearn.metrics import r2_score
from xgboost import XGBRegressor
import numpy as np
import time
import matplotlib.pyplot as plt

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'

print("--- Genomic Prediction with XGBoost ---")
print("   (Comparing to Ridge R^2: 0.6185)")
start_time = time.time()

# --- 2. Load the Dataset ---
print(f"\n[Status] Loading dataset from '{DATASET_FILE}'...")
try:
    df = pd.read_csv(DATASET_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{DATASET_FILE}' was not found.")
    exit()

# Set the 'Sample_ID' column as the index
df.set_index(df.columns[0], inplace=True)
print(f"[Status] Successfully loaded dataset with {df.shape[0]} samples and {df.shape[1]} total columns.")

# --- 3. Prepare Data for Modeling (Identical to before) ---
print("\n[Status] Preparing data for modeling...")
y = df[TARGET_VARIABLE]

# List of all 12 phenotype columns to be dropped
all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]

# X will contain ONLY genetic data (SUBPOPULATION + SNPs)
X = df.drop(columns=columns_to_drop)

# One-hot encode the categorical 'SUBPOPULATION' column
print("[Status] One-hot encoding 'SUBPOPULATION' feature...")
X = pd.get_dummies(X, columns=['SUBPOPULATION'])

# Impute missing values (e.g., the 'NaN' from "Empty" SNP data)
if X.isnull().sum().sum() > 0:
    print(f"[Status] {X.isnull().sum().sum()} missing values detected. Imputing with column mean...")
    X = X.fillna(X.mean())
else:
    print("[Status] No missing values found in features.")

print(f"[Status] Final feature matrix shape (X): {X.shape}")

# --- 4. Train and Evaluate XGBoost Model ---
print("\n[Status] Setting up XGBoost Regressor with 5-fold cross-validation...")

# We will use a reasonably strong, default XGBoost model
# n_jobs=-1 uses all your computer's cores to speed up training
model = XGBRegressor(n_estimators=100, random_state=42, n_jobs=-1)

cv = KFold(n_splits=5, shuffle=True, random_state=42)

print("[Status] Training model (this may take a few minutes)...")
# Get the R-squared score from each of the 5 folds
scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
print("[Status] Model training complete.")


# --- 5. Report Model Performance ---
print("\n--- Model Evaluation Results ---")
print(f"XGBoost R-squared (R²) scores from 5 folds: {[f'{s:.4f}' for s in scores]}")
print(f"Mean R-squared (R²): {scores.mean():.4f}")
print(f"Std Dev of R-squared: {scores.std():.4f}")

# --- 6. Visualization ---
print("\n[Status] Generating prediction plot...")
# We run cross_val_predict to get the predictions for the plot
predictions = cross_val_predict(model, X, y, cv=cv)

plt.figure(figsize=(8, 8))
plt.scatter(y, predictions, alpha=0.6)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--', color='red', lw=2)
plt.xlabel("Actual Values")
plt.ylabel("Predicted Values")
plt.title(f"Cross-Validated Prediction vs. Actual for {TARGET_VARIABLE} (XGBoost)")
plt.savefig('prediction_plot_xgb.png')
print("[Status] Plot saved to prediction_plot_xgb.png")


end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")