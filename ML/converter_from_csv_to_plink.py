import pandas as pd

# --- Configuration ---
INPUT_CSV_FILE = 'C:/Users/nitin/Desktop/Code/Project 14A/datasets/genotype_data/100k_ld_imputed.csv'
OUTPUT_PREFIX = 'genomic_full' 

print(f"Reading data from '{INPUT_CSV_FILE}'...")
print("This may take a moment for a 1GB file...")

try:
    # --- FIX 1: Changed index_col=2 to index_col=0 ---
    # Your sample ID ("B001") is in the first column.
    df = pd.read_csv(INPUT_CSV_FILE, index_col=0)
    
except FileNotFoundError:
    print(f"Error: The file '{INPUT_CSV_FILE}' was not found.")
    exit()
except Exception as e:
    print(f"An error occurred during file reading: {e}")
    exit()

# --- FIX 2: Removed the line `df = df.iloc[:, 2:]` ---
# We don't need this, as all columns are now SNPs.

print("File read successfully. Processing SNPs...")

# --- 1. Create the .map file ---
# This part is correct. It creates a map of all your SNP columns.
print(f"Creating '{OUTPUT_PREFIX}.map' file...")
with open(f'{OUTPUT_PREFIX}.map', 'w') as map_file:
    # We use 'df.columns' which now *only* contains SNP IDs
    for snp_id in df.columns:
        # Format: (Chromosome) (SNP_ID) (Genetic_Dist) (Position)
        # We'll put '1' for Chromosome and '0' for Genetic_Dist
        # and re-use the snp_id for position.
        map_file.write(f'1\t{snp_id}\t0\t{snp_id}\n')

# --- 2. Create the .ped file ---
# This logic is also correct.
print(f"Creating '{OUTPUT_PREFIX}.ped' file...")
with open(f'{OUTPUT_PREFIX}.ped', 'w') as ped_file:
    # We use 'df.iterrows()' which gives (sample_id, row_data)
    for sample_id, row_data in df.iterrows():
        # Format: (Fam_ID) (Sample_ID) (Pat_ID) (Mat_ID) (Sex) (Pheno)
        # We'll use sample_id for both, and '0' for others.
        ped_header = f'{sample_id} {sample_id} 0 0 0 -9' 
        # Using -9 for phenotype (standard for 'missing')
        
        ped_file.write(ped_header)

        genotypes = []
        for genotype in row_data:
            if genotype == 1:
                genotypes.append('A A')  # Homozygous 1
            elif genotype == -1:
                genotypes.append('G G')  # Homozygous 2
            elif genotype == 0:
                genotypes.append('A G')  # Heterozygous
            else:
                # This will catch the '0.0065...' value we saw
                # and any other strange data, coding it as 'missing'
                genotypes.append('0 0') 
        
        ped_file.write(' ' + ' '.join(genotypes) + '\n')

print("\nConversion complete!")
print(f"You should now have two new files: '{OUTPUT_PREFIX}.ped' and '{OUTPUT_PREFIX}.map'.")