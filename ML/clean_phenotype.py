import pandas as pd
from sklearn.impute import SimpleImputer

# --- Configuration ---
INPUT_FILE = 'GP_temp.csv'
OUTPUT_FILE = 'GP_full.csv'
PHENOTYPE_COLUMN_COUNT = 12

try:
    print(f"Loading dataset: {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)

    # --- 1. Separate the Data ---
    
    # Column 0: The Sample ID
    col_id = df.columns[0]
    df_ids = df[[col_id]]
    
    # Columns 1 to 12: The Phenotypes (with missing data)
    pheno_cols = df.columns[1 : 1 + PHENOTYPE_COLUMN_COUNT]
    df_pheno = df[pheno_cols]
    
    # Columns 13 onwards: The Genotypes (already clean)
    geno_cols = df.columns[1 + PHENOTYPE_COLUMN_COUNT :]
    df_geno = df[geno_cols]

    print(f"Data separated:")
    print(f"  ID: {df_ids.shape}")
    print(f"  Phenotypes (to impute): {df_pheno.shape}")
    print(f"  Genotypes (clean): {df_geno.shape}")

    # --- 2. Create and Fit the Imputer ---
    # We will use the 'median' strategy, which is robust to outliers.
    imputer = SimpleImputer(strategy='median')

    print("\nFitting imputer to find medians...")
    # Fit the imputer on the phenotype data
    imputer.fit(df_pheno)

    # --- 3. Transform (Fill) the Data ---
    print("Transforming data to fill missing values...")
    # The imputer returns a NumPy array, so we'll convert it back to a DataFrame
    df_pheno_imputed = pd.DataFrame(
        imputer.transform(df_pheno),
        columns=pheno_cols  # Put the column names back
    )

    # --- 4. Recombine and Save ---
    print("Recombining all parts...")
    # Use join, which works on the (identical) row index
    final_df = df_ids.join(df_pheno_imputed).join(df_geno)

    print(f"\n--- Imputation Complete! ---")
    print(f"Final dataset shape: {final_df.shape}")
    
    # Final check
    missing_check = final_df[pheno_cols].isnull().sum().sum()
    print(f"Total remaining missing phenotype values: {missing_check}")

    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSuccessfully saved 100% clean dataset to: {OUTPUT_FILE}")

except FileNotFoundError:
    print(f"ERROR: File not found. Please make sure '{INPUT_FILE}' is in the same directory.")
except Exception as e:
    print(f"An error occurred: {e}")