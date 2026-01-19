import pandas as pd
import os

# --- Configuration ---
large_genotype_file = './datasets/genotype_data/100k_ld_imputed.csv'
filter_file = './ind1a/merged_snp_data_by_variety_name.csv'
output_file = 'final_merged_imputed_genotypes.csv'

# Columns to use and add
key_col_in_filter_file = 'ASSAY ID'
cols_to_add = ['VARIETY_ID', 'ACCESSION']

# Chunk size for the 1GB file
chunk_size = 100000
# ---------------------

def normalize_id(assay_id):
    """Converts 'IRIS_313.8265' or 'IRIS 313-11422' to 'IRIS-313-8265'."""
    if not isinstance(assay_id, str):
        return None
    return assay_id.strip().replace(' ', '-').replace('_', '-').replace('.', '-')

# --- Main Script ---
print("--- Filtering Large File and Merging Columns ---")

# Step 1: Prepare a lookup table from the smaller filter file.
try:
    print(f"\n[1/3] Creating lookup table from '{filter_file}'...")
    filter_df = pd.read_csv(filter_file)
    
    # Ensure all necessary columns exist
    required_cols = [key_col_in_filter_file] + cols_to_add
    if not all(col in filter_df.columns for col in required_cols):
        print("\n--- ERROR ---")
        print(f"One or more required columns were not found in '{filter_file}'.")
        print(f"Required: {required_cols}")
        print(f"Available: {filter_df.columns.tolist()}")
        exit()
    
    # Create the normalized ID column to use as a merge key
    filter_df['normalized_id'] = filter_df[key_col_in_filter_file].apply(normalize_id)
    
    # Create a clean lookup table with only the columns we need
    lookup_table = filter_df[['normalized_id'] + cols_to_add].dropna(subset=['normalized_id']).drop_duplicates()
    print(f"  -> Lookup table created with {len(lookup_table)} unique entries.")

except FileNotFoundError:
    print(f"Error: The filter file '{filter_file}' was not found.")
    exit()

# Step 2: Process the large genotype file in chunks and merge.
try:
    print(f"\n[2/3] Processing and merging '{large_genotype_file}' in chunks...")
    chunk_iterator = pd.read_csv(large_genotype_file, chunksize=chunk_size, low_memory=False)
    
    is_first_chunk = True
    total_matches = 0
    
    for i, chunk in enumerate(chunk_iterator):
        id_column_in_large_file = chunk.columns[0]
        original_chunk_cols = chunk.columns.tolist()
        
        # Create the normalized ID in the chunk to match the lookup table
        chunk['normalized_id'] = chunk[id_column_in_large_file].apply(normalize_id)
        
        # Merge the chunk with the lookup table to filter and add columns
        # 'how="inner"' ensures we only keep rows that match.
        merged_chunk = pd.merge(chunk, lookup_table, on='normalized_id', how='inner')
        
        if not merged_chunk.empty:
            num_matches_in_chunk = len(merged_chunk)
            total_matches += num_matches_in_chunk
            print(f"  -> Processing chunk {i+1}... Found and merged {num_matches_in_chunk} rows.")
            
            # Reorder columns: put new info first, then original data
            final_cols = cols_to_add + original_chunk_cols
            merged_chunk = merged_chunk[final_cols]
            
            # Write to the output file
            if is_first_chunk:
                merged_chunk.to_csv(output_file, index=False, mode='w') # Write with header
                is_first_chunk = False
            else:
                merged_chunk.to_csv(output_file, index=False, mode='a', header=False) # Append
        else:
             print(f"  -> Processing chunk {i+1}... Found 0 matches.")
    
    print("  -> Finished processing all chunks.")

except FileNotFoundError:
    print(f"Error: The large genotype file '{large_genotype_file}' was not found.")
    exit()

# Step 3: Final confirmation.
if os.path.exists(output_file):
    print(f"\n[3/3] ✅ Success! Merged a total of {total_matches} rows.")
    print(f"The final dataset with added columns is saved to '{output_file}'.")
else:
     print("\n--- Notice ---")
     print("Processing complete, but no matching rows were found. The output file was not created.")