import pandas as pd

# --- Configuration ---
GENOTYPE_FILE = 'plink/final_genotypes_matrix.raw'
PHENO_FILE = r'C:\Users\nitin\Desktop\Code\Project 14A\datasets\real_trait_data\real_quantitative_traits.csv'
OUTPUT_FILE = 'GP_full.csv' # Changed back to your new name

print(f"Loading genotypes from {GENOTYPE_FILE}...")
# --- 1. Load Clean Genotype Data ---
# Use sep='\s+' as the warning suggested
gen_df = pd.read_csv(GENOTYPE_FILE, sep=r'\s+')

# Keep only the sample ID ('IID') and the SNP data (cols 6 onwards)
snp_columns = gen_df.columns[6:] # This is our list of genotype cols
gen_df = gen_df[['IID'] + list(snp_columns)]
print(f"Genotype data loaded: {gen_df.shape[0]} samples, {gen_df.shape[1]-1} SNPs")


# --- 2. Load Phenotype Data ---
print(f"Loading phenotypes from {PHENO_FILE}...")
pheno_df = pd.read_csv(PHENO_FILE)

# The sample ID is in 'Unnamed: 0'. Let's rename it for clarity.
pheno_df.rename(columns={'Unnamed: 0': 'Sample_ID'}, inplace=True)

# *** NEW *** Get the list of phenotype columns *before* the merge
pheno_col_list = [col for col in pheno_df.columns if col != 'Sample_ID']
print(f"Phenotype data loaded: {pheno_df.shape[0]} samples, {len(pheno_col_list)} traits")


# --- 3. Perform the Final Merge ---
print("Merging data on matching sample IDs...")

# We use an "inner" merge, as in your plan.
final_dataset = pd.merge(
    gen_df,
    pheno_df,
    left_on='IID',      # ID from genotype file
    right_on='Sample_ID'  # ID from phenotype file
)

# --- 4. Re-order Columns and Save ---
print("Re-ordering columns for final dataset...")

# *** NEW *** Define the desired column order
# [Sample_ID] + [Phenotype 1, Phenotype 2...] + [SNP 1, SNP 2...]
new_column_order = ['Sample_ID'] + pheno_col_list + list(snp_columns)

# *** NEW *** Apply the new order
final_dataset = final_dataset[new_column_order]

print(f"\n--- Merge Complete! ---")
print(f"Final dataset shape: {final_dataset.shape}")
print(f"Total samples: {final_dataset.shape[0]} (This should be 1011)")
print(f"Total columns: {final_dataset.shape[1]}")

final_dataset.to_csv(OUTPUT_FILE, index=False)
print(f"\nSuccessfully saved final dataset to: {OUTPUT_FILE}")
print(f"Column order is now: Sample_ID, Phenotypes..., Genotypes...")