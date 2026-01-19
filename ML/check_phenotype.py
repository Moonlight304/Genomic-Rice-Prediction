import pandas as pd

# The file path you provided
pheno_file = 'C:/Users/nitin/Desktop/Code/Project 14A/datasets/real_trait_data/real_quantitative_traits.csv'

try:
    print(f"--- Inspecting Phenotype File ---")
    print(f"File: {pheno_file}\n")

    # Read just the header to get column names
    df_head = pd.read_csv(pheno_file, nrows=0)
    print("Column Names:")
    print(list(df_head.columns))
    print("\n")

    # Read the first 5 rows to see the data format
    df_sample = pd.read_csv(pheno_file, nrows=5)
    print("--- First 5 Rows (for context) ---")
    print(df_sample)

except FileNotFoundError:
    print(f"ERROR: File not found. Please check the path:\n{pheno_file}")
except Exception as e:
    print(f"An error occurred: {e}")