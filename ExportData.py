import pandas as pd

# Load the CSV file
file_path = 'output.csv'
df = pd.read_csv(file_path, encoding='ISO-8859-1')

# Define the postal codes for Bretagne and Pays de la Loire
bretagne_postal_codes = ['22', '29', '35', '56']
pays_de_la_loire_postal_codes = ['44', '49', '53', '72', '85']

# Filter for Bretagne
bretagne_df = df[df['postal_code'].apply(lambda x: str(x).startswith(tuple(bretagne_postal_codes)))]

# Filter for Pays de la Loire
pdl_df = df[df['postal_code'].apply(lambda x: str(x).startswith(tuple(pays_de_la_loire_postal_codes)))]

# Remove duplicates in both dataframes
bretagne_df = bretagne_df.drop_duplicates()
pdl_df = pdl_df.drop_duplicates()

# Save the filtered dataframes to new CSV files
bretagne_file_path = 'bretagne_filtered.csv'
pdl_file_path = 'pdl_filtered.csv'

bretagne_df.to_csv(bretagne_file_path, index=False)
pdl_df.to_csv(pdl_file_path, index=False)

print(f"Bretagne filtered data saved to {bretagne_file_path}")
print(f"Pays de la Loire filtered data saved to {pdl_file_path}")
