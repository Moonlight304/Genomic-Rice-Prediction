import csv

# file_path = 'snp3kvars-CHR1-1-100000-8321031374028163257.csv'
file_path = 'GP_full.csv'

try:
    with open(file_path, 'r') as f:
        header = f.readline().strip()
        first_data_row = f.readline().strip()
        second_data_row = f.readline().strip()  # <-- added line

    print("--- Header (First 200 characters) ---")
    print(header[:200])
    print("\n")
    
    print("--- First Data Row (First 200 characters) ---")
    print(first_data_row[:200])
    print("\n")

    print("--- Second Data Row (First 200 characters) ---")
    print(second_data_row[:200])
    print("\n")

    header_list = header.split(',')
    print(f"Total number of columns (including sample ID): {len(header_list)}")

    subpop_cols = [col for col in header_list if 'subpop' in col.lower()]
    if subpop_cols:
        print(f"Found potential subpopulation column(s): {subpop_cols}")
    else:
        print("No obvious 'subpopulation' column found in the header.")

except FileNotFoundError:
    print(f"ERROR: File not found at {file_path}")
except Exception as e:
    print(f"An error occurred: {e}")
