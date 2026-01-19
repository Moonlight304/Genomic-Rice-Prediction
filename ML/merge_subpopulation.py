import pandas as pd

# --- Configuration ---
MAIN_DATA_FILE = 'GP_full.csv'
METADATA_FILE = 'snp3kvars-CHR1-1-100000-8321031374028163257.csv'
PHENOTYPE_COLUMN_COUNT = 12

try:
    # --- 1. Load your main dataset ---
    print(f"Loading main dataset: {MAIN_DATA_FILE}...")
    df_main = pd.read_csv(MAIN_DATA_FILE)

    # Store the column names for later
    pheno_cols = df_main.columns[1 : 1 + PHENOTYPE_COLUMN_COUNT]
    geno_cols = df_main.columns[1 + PHENOTYPE_COLUMN_COUNT :]
    
    print(f"Loaded {len(df_main)} samples.")

    # --- 2. Load the metadata file ---
    print(f"Loading metadata: {METADATA_FILE}...")
    
    cols_to_use = ['ASSAY ID', 'SUBPOPULATION']
    
    df_meta = pd.read_csv(
        METADATA_FILE,
        usecols=cols_to_use,
        header=0,      # The header is on the first line (index 0)
        skiprows=[1]   # Skip the *second* line (index 1)
    )

    # --- 3. Fix the ID Mismatch (Two-step fix) ---
    df_meta['ASSAY ID'] = df_meta['ASSAY ID'].str.replace(' ', '_')
    df_meta['ASSAY ID'] = df_meta['ASSAY ID'].str.replace('-', '.')
    
    df_meta.rename(columns={'ASSAY ID': 'Sample_ID'}, inplace=True)
    df_meta = df_meta.drop_duplicates(subset=['Sample_ID'])
    print("Metadata loaded and cleaned.")

    # --- 4. Merge the data ---
    print("Merging subpopulation data into main dataset...")
    
    # Use a 'left' merge to keep all 1011 of your main samples
    df_final = pd.merge(
        df_main,
        df_meta,
        on='Sample_ID',
        how='left' # Keep all rows from df_main
    )

    # --- 5. Re-order Columns and Save ---
    # Define the new, logical order
    new_column_order = ['Sample_ID', 'SUBPOPULATION'] + list(pheno_cols) + list(geno_cols)
    
    # Apply the new order
    df_final = df_final[new_column_order]
    
    # --- 6. Overwrite the Original File ---
    df_final.to_csv(MAIN_DATA_FILE, index=False)
    
    print(f"\n--- Success! ---")
    print(f"Successfully updated {MAIN_DATA_FILE}")
    print(f"New shape: {df_final.shape}")
    print(f"The 'SUBPOPULATION' column has been added.")

except FileNotFoundError as e:
    print(f"ERROR: File not found. {e}")
except ValueError as e:
    print(f"ERROR: A required column was not found. {e}")
except Exception as e:
    print(f"An error occurred: {e}")