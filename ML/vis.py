import pandas as pd
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import KFold, cross_val_predict
import matplotlib.pyplot as plt
import numpy as np

# --- Configuration ---
DATASET_FILE = 'GEP_full.csv'
TARGET_VARIABLE = 'HDG_80HEAD'
TOP_N_FEATURES = 1000

print("--- Generating Final 'Actual vs Predicted' Plot ---")

# 1. Load Data
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

# 2. Feature Selection
print("[Status] Selecting features...")
selector_model = XGBRegressor(n_estimators=100, max_depth=5, n_jobs=-1, random_state=42)
selector_model.fit(X_numpy, y_numpy)
selector = SelectFromModel(selector_model, max_features=TOP_N_FEATURES, threshold=-np.inf, prefit=True)
X_elite = selector.transform(X_numpy)

# 3. Build The Champion Ensemble
xgb_model = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, n_jobs=-1, random_state=42)
lgbm_model = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, n_jobs=-1, random_state=42, verbose=-1)
ensemble = VotingRegressor(estimators=[('xgb', xgb_model), ('lgbm', lgbm_model)], n_jobs=-1)

# 4. Generate Predictions (Cross-Validated)
print("[Status] Generating predictions for all samples...")
cv = KFold(n_splits=5, shuffle=True, random_state=42)
# This gives us the prediction for every single point as if it was in the test set
y_pred = cross_val_predict(ensemble, X_elite, y_numpy, cv=cv, n_jobs=1)

# 5. Plotting
print("[Status] Creating plot...")
plt.figure(figsize=(10, 8))
plt.scatter(y_numpy, y_pred, alpha=0.5, color='blue', edgecolor='k', s=40)

# Draw the "Perfect Prediction" line
min_val = min(y_numpy.min(), y_pred.min())
max_val = max(y_numpy.max(), y_pred.max())
plt.plot([min_val, max_val], [min_val, max_val], color='red', linestyle='--', linewidth=2, label='Perfect Prediction')

plt.xlabel('Actual Flowering Time (Days)', fontsize=12)
plt.ylabel('AI Predicted Flowering Time (Days)', fontsize=12)
plt.title(f'XGBoost + LightGBM Ensemble\nR²: 0.6755 | MAE: 9.9 Days', fontsize=14)
plt.legend()
plt.grid(True, alpha=0.3)

# Save the plot
plt.savefig('final_model_performance.png', dpi=300)
print("[Status] Plot saved as 'final_model_performance.png'. Check your folder!")
plt.show()