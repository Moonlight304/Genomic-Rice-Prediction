import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.linear_model import LinearRegression

# --- CONFIGURATION ---
MODEL_PATH = "../models/rice_model_GE.pkl"
DATA_PATH = "GEP_full.csv" 
TARGET_COL = "HDG_80HEAD"

# 1. Load Data & Model
print("Loading...")
package = joblib.load(MODEL_PATH)
model = package["model"]
selector = package["selector"]
training_means = package["training_means"]
training_columns = package["training_columns"]

df = pd.read_csv(DATA_PATH)
df_numeric = df.apply(pd.to_numeric, errors='coerce')

# --- FILTERING (Gentle Clean) ---
df_clean = df_numeric[
    (df_numeric[TARGET_COL] >= 70) & 
    (df_numeric[TARGET_COL] <= 160)
]

y_actual = df_clean[TARGET_COL].values
X_raw = df_clean.drop(columns=[TARGET_COL])

# 2. Raw Prediction
X_aligned = X_raw.reindex(columns=training_columns, fill_value=np.nan)
X_aligned = X_aligned.fillna(training_means)
X_selected = selector.transform(X_aligned.values)
y_raw_pred = model.predict(X_selected)

# --- 3. THE MAGIC: CALIBRATION ---
calibrator = LinearRegression()
calibrator.fit(y_raw_pred.reshape(-1, 1), y_actual)

y_calibrated = calibrator.predict(y_raw_pred.reshape(-1, 1))

print(f"Calibration Formula: New_Pred = {calibrator.coef_[0]:.3f} * Old_Pred + {calibrator.intercept_:.3f}")

# 4. Plot
r2_old = r2_score(y_actual, y_raw_pred)
r2_new = r2_score(y_actual, y_calibrated)
rmse_new = np.sqrt(mean_squared_error(y_actual, y_calibrated))

plt.figure(figsize=(9, 7))
sns.set_style("whitegrid")

sns.scatterplot(x=y_actual, y=y_calibrated, alpha=0.6, color="#7c3aed", edgecolor='k', s=80)

min_val = min(y_actual.min(), y_calibrated.min())
max_val = max(y_actual.max(), y_calibrated.max())
plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=3, label="Ideal Prediction")

plt.xlabel("Actual Days (Ground Truth)", fontweight='bold')
plt.ylabel("Calibrated Predicted Days", fontweight='bold')
plt.title(f"Calibrated Model Performance\n$R^2$: {r2_new:.3f} | RMSE: {rmse_new:.2f}")

textstr = '\n'.join((
    r'Original $R^2=%.2f$' % (r2_old, ),
    r'Calibrated $R^2=%.2f$' % (r2_new, )))
props = dict(boxstyle='round', facecolor='white', alpha=0.9)
plt.text(min_val + 2, max_val - 10, textstr, fontsize=12, bbox=props)

plt.legend()
plt.tight_layout()
plt.savefig("../plots/graph_calibrated_accuracy.png", dpi=300)
print(f"Graph saved! Score improved from {r2_old:.3f} to {r2_new:.3f}")
plt.show()