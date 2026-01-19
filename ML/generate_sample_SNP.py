import pandas as pd

# Load your full dataset
df = pd.read_csv('GEP_full.csv')

# Take the first 5 rows
test_df = df.head(5).copy()

# Remove the target variable (simulating a real "blind" test)
if 'HDG_80HEAD' in test_df.columns:
    test_df = test_df.drop(columns=['HDG_80HEAD'])

# Save to a new CSV
test_df.to_csv('real_test_sample.csv', index=False)

print("Created 'real_test_sample.csv'. Upload this to your website!")