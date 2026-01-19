import pandas as pd

# --- Configuration ---
MAIN_DATA_FILE = 'GP_full.csv'
METADATA_FILE = 'snp3kvars-CHR1-1-100000-8321031374028163257.csv'

try:
    # --- 1. Load your 1011 sample IDs from the main file ---
    print(f"Loading sample IDs from: {MAIN_DATA_FILE}...")
    
    main_ids = pd.read_csv(MAIN_DATA_FILE, usecols=['Sample_ID'])['Sample_ID']
    main_id_set = set(main_ids)
    print(f"Loaded {len(main_id_set)} unique IDs.")


    # --- 2. Load the metadata file ---
    print(f"Loading metadata: {METADATA_FILE}...")
    
    cols_to_use = ['ASSAY ID', 'SUBPOPULATION']
    
    df_meta = pd.read_csv(
        METADATA_FILE,
        usecols=cols_to_use,
        header=0,      # The header is on the first line (index 0)
        skiprows=[1]   # Skip the *second* line (index 1)
    )

    # --- 3. Fix the ID Mismatch (TWO-STEP FIX) ---
    # Step 3a: Replace the space with an underscore
    df_meta['ASSAY ID'] = df_meta['ASSAY ID'].str.replace(' ', '_')
    
    # --- THIS IS THE NEW FIX ---
    # Step 3b: Replace the dash with a dot
    df_meta['ASSAY ID'] = df_meta['ASSAY ID'].str.replace('-', '.')
    # --- END OF FIX ---
    
    df_meta.rename(columns={'ASSAY ID': 'Sample_ID'}, inplace=True)
    df_meta = df_meta.drop_duplicates(subset=['Sample_ID'])
    print("Metadata loaded and cleaned.")

    # --- 4. Filter metadata to ONLY your samples ---
    matched_meta = df_meta[df_meta['Sample_ID'].isin(main_id_set)]

    # --- 5. Print the Final Counts ---
    print("\n" + "="*40)
    print("   Subpopulation Counts in Your Data   ")
    print("="*40)
    
    subpop_counts = matched_meta['SUBPOPULATION'].value_counts(dropna=False)
    print(subpop_counts)
    
    print("\n---")
    print(f"Total samples found in metadata: {len(matched_meta)}")
    if len(main_id_set) != len(matched_meta):
        print(f"Note: {len(main_id_set) - len(matched_meta)} samples were not found in the metadata file.")


except FileNotFoundError as e:
    print(f"ERROR: File not found. {e}")
except ValueError as e:
    print(f"ERROR: A required column was not found. {e}")
except Exception as e:
    print(f"An error occurred: {e}")