import duckdb
import pandas as pd

parquet_file = 'data/redcap_export_11_20250221220411_d318ba96-4548-44c5-a55d-1b9b6b51388a.parquet'
data_dict_file = 'data_dictionaries/AdultHIVProject1_1_DataDict_2024-12-11.csv'
output_csv_file = 'data/pivoted_project_1_1_data.csv'  # Output file path

# Read the CSV to get the field names
# exclude any fields that are  identifiers
df_csv = pd.read_csv(data_dict_file)
field_names = df_csv[df_csv['Identifier?'].isnull()]['Variable / Field Name'].tolist()

# Construct the subquery with dynamic field_names filter
field_names_str = "', '".join(field_names)
subquery = f"""
    (
        SELECT record, field_name, value
        FROM read_parquet('{parquet_file}')
        WHERE field_name IN ('{field_names_str}')
    )
"""

# Construct the PIVOT query
sql = f"""
PIVOT
    {subquery}
ON field_name
USING MAX(value)
GROUP BY record;
"""

# Execute the query and write to CSV
con = duckdb.connect()
result_df = con.execute(sql).df()
result_df.to_csv(output_csv_file, index=False)
con.close()

print(f"Pivoted data written to: {output_csv_file}")