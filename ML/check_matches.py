import pandas as pd

# --- File Paths ---
GENOTYPE_FILE = './plink/final_genotypes_matrix.raw'
PHENO_FILE = 'C:/Users/nitin/Desktop/Code/Project 14A/datasets/real_trait_data/real_quantitative_traits.csv'

try:
    # --- 1. Load Genotype IDs ---
    # Load *only* the 'IID' column (the sample ID)
    gen_ids = pd.read_csv(
        GENOTYPE_FILE,
        delim_whitespace=True,
        usecols=['IID']
    )['IID']
    
    # Convert to a set for fast lookup
    gen_id_set = set(gen_ids)
    print(f"Loaded {len(gen_id_set)} unique IDs from genotype file.")

    # --- 2. Load Phenotype IDs ---
    # Load *only* the 'Unnamed: 0' column (the sample ID)
    pheno_ids = pd.read_csv(
        PHENO_FILE,
        usecols=['Unnamed: 0']
    )['Unnamed: 0']
    
    # Convert to a set
    pheno_id_set = set(pheno_ids)
    print(f"Loaded {len(pheno_id_set)} unique IDs from phenotype file.")

    # --- 3. Find the Matches ---
    matching_ids = gen_id_set.intersection(pheno_id_set)
    num_matches = len(matching_ids)

    print("\n" + "="*30)
    print(f"   Result: Found {num_matches} matching IDs.")
    print("="*30 + "\n")

    # --- 4. Diagnostic Info (Format Check) ---
    # This section checks the format by printing examples
    print("--- Diagnostic: First 5 IDs (Format Check) ---")
    print(f"Genotype IDs (IID): {list(gen_id_set)[:5]}")
    print(f"Phenotype IDs (Unnamed: 0): {list(pheno_id_set)[:5]}")

    if num_matches == 0:
        print("\nWARNING: No matches found. The ID formats look different.")
        print("We may need a 'key file' to map one ID format to the other.")
    else:
        print(f"\nSuccess! Found {num_matches} samples to merge.")
        print(f"Example matching ID: {list(matching_ids)[0]}")


except FileNotFoundError as e:
    print(f"ERROR: File not found. {e}")
except ValueError as e:
    print(f"ERROR: A column is missing. {e}")
except Exception as e:
    print(f"An error occurred: {e}")