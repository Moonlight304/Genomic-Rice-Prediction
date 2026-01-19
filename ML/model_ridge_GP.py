import pandas as pd
from sklearn.model_selection import KFold, cross_val_score
from sklearn.linear_model import RidgeCV
from sklearn.metrics import r2_score
import numpy as np
import time
import matplotlib.pyplot as plt

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'

print("--- Genomic Prediction with Ridge Regression ---")
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

# --- 3. Prepare Data for Modeling ---
print("\n[Status] Preparing data for modeling...")
y = df[TARGET_VARIABLE]

# *** MODIFIED ***
# Corrected list of all 12 phenotype columns to be dropped from the features (X).
# We are predicting 'HDG_80HEAD' from genetics ONLY, so we must drop all other phenotypes.
all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
# Find which of these columns are actually in the dataframe to avoid errors
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]

# X will contain ONLY genetic data (SUBPOPULATION + SNPs)
X = df.drop(columns=columns_to_drop)

# *** NEW STEP ***
# One-hot encode the categorical 'SUBPOPULATION' column
# This turns text like 'aus', 'ind1B' into numeric 0/1 columns
print("[Status] One-hot encoding 'SUBPOPULATION' feature...")
X = pd.get_dummies(X, columns=['SUBPOPULATION'])
print(f"[Status] Features (X) after encoding: {X.shape[1]} (SNPs + Subpopulations)")

# *** MODIFIED ***
# Impute missing values (e.g., the 'NaN' from "Empty" SNP data)
# This step must come *after* one-hot encoding
if X.isnull().sum().sum() > 0:
    print(f"[Status] {X.isnull().sum().sum()} missing values detected. Imputing with column mean...")
    X = X.fillna(X.mean())
else:
    print("[Status] No missing values found in features.")

# --- 4. Train and Evaluate Ridge Regression Model ---
print("\n[Status] Setting up Ridge Regression with built-in cross-validation...")
# Using a small, fast range of alphas for testing
alphas = np.logspace(-2, 4, 10) 

cv = KFold(n_splits=5, shuffle=True, random_state=42)

# Using 'neg_mean_squared_error' is more stable for regression
model = RidgeCV(alphas=alphas, cv=cv, scoring='neg_mean_squared_error')

print("[Status] Training model and finding best regularization strength...")
model.fit(X, y)
print("[Status] Model training complete.")


# --- 5. Report Model Performance ---
print("\n--- Model Evaluation Results ---")

# Calculate R-squared from the best model
# We must re-calculate R^2. The 'best_score_' is neg_mean_squared_error.
print("[Status] Calculating R-squared on cross-validation predictions...")
from sklearn.model_selection import cross_val_predict
predictions = cross_val_predict(model, X, y, cv=cv)
r2 = r2_score(y, predictions)

print(f"Cross-Validated R-squared (R²): {r2:.4f}")
print(f"Optimal Alpha (Regularization Strength): {model.alpha_:.4f}")

# --- 6. Visualization ---
print("\n[Status] Generating prediction plot...")
plt.figure(figsize=(8, 8))
plt.scatter(y, predictions, alpha=0.6)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--', color='red', lw=2)
plt.xlabel("Actual Values")
plt.ylabel("Predicted Values")
plt.title(f"Cross-Validated Prediction vs. Actual for {TARGET_VARIABLE} (Ridge)")
plt.savefig('prediction_plot_ridge.png')
print("[Status] Plot saved to prediction_plot_ridge.png")


end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")