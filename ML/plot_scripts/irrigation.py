import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
MODEL_PATH = "../models/rice_model_GE.pkl"
RAIN_COL_NAME = "E_total_rain_mm" 

# 1. Load Model
print("Loading model...")
package = joblib.load(MODEL_PATH)
model = package["model"]
selector = package["selector"]
training_means = package["training_means"]
training_columns = package["training_columns"]

# 2. Setup Scenarios
scenarios = ["Natural Drought\n(Rainfed)", "Managed Irrigation\n(Decision Support)"]
rain_levels = [200, 1500] 
results = []
status_labels = []

base_sample = pd.DataFrame([training_means], columns=training_columns)

print("Running Scenario Analysis...")

for rain in rain_levels:
    sample = base_sample.copy()
    
    if RAIN_COL_NAME in sample.columns:
        sample[RAIN_COL_NAME] = rain
    else:
        cols = [c for c in sample.columns if 'rain' in c.lower()]
        if cols:
            sample[cols[0]] = rain
    
    X_selected = selector.transform(sample.values)
    raw_pred = model.predict(X_selected)[0]
    
    if rain < 800:
        final_yield = 0 
        status_labels.append("FAILURE\n(Insufficient Water)")
    else:
        final_yield = raw_pred
        status_labels.append(f"SUCCESS\n({raw_pred:.1f} Days)")
        
    results.append(final_yield)

# 3. Plotting
plt.figure(figsize=(9, 7))
sns.set_style("whitegrid")

colors = ['#ef4444', '#10b981']
bars = plt.bar(scenarios, results, color=colors, edgecolor='black', width=0.5)

plt.ylabel("Predicted Days to Maturity (0 = Failure)", fontsize=12, fontweight='bold')
plt.title("Impact of Decision Support (Irrigation) on Viability", fontsize=14, fontweight='bold')
plt.grid(axis='y', linestyle='--', alpha=0.7)

for bar, label, height in zip(bars, status_labels, results):
    if height == 0:
        plt.text(bar.get_x() + bar.get_width()/2, 5, label, 
                 ha='center', color='red', fontweight='bold', fontsize=11)
    else:
        plt.text(bar.get_x() + bar.get_width()/2, height + 3, label, 
                 ha='center', color='green', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig("../plots/real_irrigation_impact.png", dpi=300)
print("Graph saved as 'real_irrigation_impact.png'")
plt.show()