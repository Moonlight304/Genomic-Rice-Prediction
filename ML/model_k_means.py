import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import time

# --- 1. Configuration ---
DATASET_FILE = 'GP_full.csv'
N_CLUSTERS = 12 # We'll look for 12 clusters to compare to the 12 subpops

print(f"--- Running K-Means Clustering on Genetic Data ---")
start_time = time.time()

# --- 2. Load the Dataset ---
print(f"\n[Status] Loading dataset from '{DATASET_FILE}'...")
try:
    df = pd.read_csv(DATASET_FILE)
except FileNotFoundError:
    print(f"Error: The dataset file '{DATASET_FILE}' was not found.")
    exit()

print(f"[Status] Successfully loaded dataset with {df.shape[0]} samples.")

# --- 3. Prepare Genetic Data for Clustering ---
# We'll cluster on the *same features* we used for modeling.
print("\n[Status] Preparing genetic features (X) for clustering...")

# Get *all* phenotype columns to drop
all_phenotype_columns = [
    'CUDI_REPRO', 'CULT_REPRO', 'CUNO_REPRO', 'GRLT', 'GRWD', 'GRWT100', 
    'HDG_80HEAD', 'LIGLT', 'LLT', 'LWD', 'PLT_POST', 'SDHT'
]
# Find which of these columns are actually in the dataframe to avoid errors
columns_to_drop = [col for col in all_phenotype_columns if col in df.columns]

# X will contain ONLY genetic data (SUBPOPULATION + SNPs)
X = df.drop(columns=columns_to_drop + ['Sample_ID'])

# One-hot encode the 'SUBPOPULATION' feature
X = pd.get_dummies(X, columns=['SUBPOPULATION'])

# Impute any missing SNP data
if X.isnull().sum().sum() > 0:
    print(f"[Status] {X.isnull().sum().sum()} missing values detected. Imputing with column mean...")
    X = X.fillna(X.mean())

# --- 4. Scale the Data (Critical for K-Means) ---
# K-Means is very sensitive to scale, so we must standardize the features.
print("[Status] Scaling features (StandardScaler)...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- 5. Run K-Means ---
print(f"[Status] Running K-Means to find {N_CLUSTERS} clusters...")
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
kmeans.fit(X_scaled)

# Get the new cluster labels for each sample
new_cluster_labels = kmeans.labels_

# --- 6. "See" the Results: Compare Clusters ---
print("\n[Status] Comparing new K-Means clusters to original Subpopulations...")

# Add the new cluster labels back to the original dataframe
df['KMeans_Cluster'] = new_cluster_labels

# Create a crosstab to see the overlap
# Rows = New K-Means Clusters
# Columns = Original, known Subpopulations
cluster_comparison = pd.crosstab(
    df['KMeans_Cluster'], 
    df['SUBPOPULATION']
)

print("\n" + "="*40)
print("--- K-Means vs. Subpopulation Comparison ---")
print("="*40)
print(cluster_comparison)
print("\n(Rows are the new K-Means clusters, Columns are the original groups)")


end_time = time.time()
print(f"\n--- Script finished in {end_time - start_time:.2f} seconds ---")