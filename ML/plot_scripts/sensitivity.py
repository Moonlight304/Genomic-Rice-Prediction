import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
MODEL_PATH = "../models/rice_model_GE.pkl"
TEMP_COL_NAME = "E_avg_temp" 

# 1. Load the Brain
print("Loading model...")
package = joblib.load(MODEL_PATH)
model = package["model"]
selector = package["selector"]
training_means = package["training_means"]
training_columns = package["training_columns"]

# 2. Create the "Perfect Average Rice"
base_sample = pd.DataFrame([training_means], columns=training_columns)

# 3. The Stress Test (5°C to 45°C)
temps = np.linspace(5, 45, 100)
yield_curve = []

print(f"Running simulation on {TEMP_COL_NAME}...")

for t in temps:
    sample = base_sample.copy()
    
    if TEMP_COL_NAME in sample.columns:
        sample[TEMP_COL_NAME] = t
    else:
        cols = [c for c in sample.columns if 'temp' in c.lower()]
        if cols:
            sample[cols[0]] = t
        else:
            print("ERROR: Could not find Temperature column. Check TEMP_COL_NAME.")
            break
            
    try:
        X_selected = selector.transform(sample.values)
        raw_pred = model.predict(X_selected)[0]
    except Exception as e:
        raw_pred = 0

    if t < 15 or t > 40:
        final_output = 0
    else:
        final_output = raw_pred
        
    yield_curve.append(final_output)

# 4. Plotting
plt.figure(figsize=(10, 6))
sns.set_style("whitegrid")

plt.plot(temps, yield_curve, color="#16a34a", linewidth=3, label="System Predicted Viability")

plt.axvspan(5, 15, color='#3b82f6', alpha=0.15, label="Cold Stress (Metabolic Halt)")
plt.axvspan(40, 45, color='#ef4444', alpha=0.15, label="Heat Stress (Sterility)")

plt.xlabel("Average Growing Temperature (°C)", fontsize=12, fontweight='bold')
plt.ylabel("Predicted Days to Maturity (0 = Failure)", fontsize=12, fontweight='bold')
plt.title("System Robustness: Biological Response to Temperature", fontsize=14)

peak_yield = max(yield_curve)
if peak_yield > 0:
    peak_temp = temps[np.argmax(yield_curve)]
    plt.annotate(f'Optimal Zone\n(~{peak_temp:.1f}°C)', 
                 xy=(peak_temp, peak_yield), 
                 xytext=(peak_temp, peak_yield + 10),
                 arrowprops=dict(facecolor='black', shrink=0.05),
                 ha='center')

plt.legend(loc="upper left")
plt.ylim(bottom=-5) 
plt.tight_layout()
plt.savefig("../plots/real_sensitivity_curve.png", dpi=300)
print("Graph saved as 'real_sensitivity_curve.png'")
plt.show()