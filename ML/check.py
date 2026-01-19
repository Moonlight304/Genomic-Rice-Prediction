import pandas as pd

# DATA_FILE="C:/Users/nitin/Desktop/Code/Project 14A/datasets/genotype_data/100k_ld_imputed.csv"
DATA_FILE="./GP_full.csv"

# Load CSV safely
df = pd.read_csv(DATA_FILE, low_memory=False)

# Get number of rows and columns
print("Rows:", df.shape[0])
print("Columns:", df.shape[1])
