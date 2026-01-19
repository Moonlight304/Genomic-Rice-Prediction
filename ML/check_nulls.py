import pandas as pd

FILE_NAME = 'GP_full.csv'
PHENOTYPE_COLUMN_COUNT = 12 

try:
    print(f"Loading dataset: {FILE_NAME}...")
    df = pd.read_csv(FILE_NAME)

    # We assume the first column is 'Sample_ID'
    # The next 12 columns (index 1 to 12) are your phenotypes
    phenotype_cols = df.columns[1 : 1 + PHENOTYPE_COLUMN_COUNT]
    print(f"Checking these {len(phenotype_cols)} columns for missing values:\n{list(phenotype_cols)}\n")

    # Calculate missing values for just those columns
    missing_data = df[phenotype_cols].isnull().sum()
    
    # Filter to show only columns that *have* missing data
    missing_data = missing_data[missing_data > 0]

    if missing_data.empty:
        print("--- Result ---")
        print("✅ Excellent! No missing values found in any phenotype columns.")
    else:
        print("--- Result: Found Missing Values ---")
        print("The following phenotype columns are missing data:\n")
        print(missing_data)
        print(f"\nTotal rows in dataset: {len(df)}")

except FileNotFoundError:
    print(f"ERROR: File not found. Please make sure '{FILE_NAME}' is in the same directory.")
except Exception as e:
    print(f"An error occurred: {e}")