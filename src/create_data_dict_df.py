import pandas as pd

def create_data_dict_df(data_dict_file_name:str, data_dict_append_file_name:str) -> pd.DataFrame:
    """
    Creates and returns the data dictionary DataFrame after reading the main data dictionary CSV 
    and appending the additional data dictionary CSV.
    Rename the columns and set the data types for all fields in the data_dict_df.

    Args:
        data_dict_file_name (str): The file name of the main data dictionary CSV.
        data_dict_append_file_name (str): The file name of the additional data dictionary CSV to append.

    Returns:
        pd.DataFrame: The combined data dictionary DataFrame.
    """
    # Read the main data dictionary CSV
    data_dict_df = pd.read_csv(data_dict_file_name, na_filter=False, dtype=str)
    # sub string the section_header to 200 characters
    data_dict_df['Section Header'] = data_dict_df['Section Header'].str[:200]
    # Read the additional data dictionary CSV and append it to the main DataFrame
    data_dict_append_df = pd.read_csv(data_dict_append_file_name, na_filter=False, dtype=str)
    data_dict_df = pd.concat([data_dict_df, data_dict_append_df], ignore_index=True)
    
    # Add a sequence number to the data dictionary
    data_dict_df.insert(0, 'sequence', range(1, len(data_dict_df) + 1))
    
    # Set sequence dtype to int
    data_dict_df['sequence'] = data_dict_df['sequence'].astype(int)
    
    # Select and rename columns
    data_dict_df = data_dict_df[['sequence', 'Variable / Field Name', 'Form Name', 'Section Header', 'Field Type', 'Field Label', 'Active', 'form_sequence_id']]
    data_dict_df = data_dict_df.rename(columns={'Variable / Field Name': 'field_name', 'Form Name': 'form_name', 
                                                'Section Header': 'section_header', 'Field Type': 'field_type', 'Field Label': 'field_label', 
                                                'Active': 'Active', 'form_sequence_id': 'form_sequence_id'})
    
    # Add CreatedOn and FileName columns
    data_dict_df['CreatedOn'] = pd.to_datetime('today').date()
    data_dict_df['FileName'] = data_dict_file_name.split('/')[-1]
    
    # Set the data types for all fields in the data_dict_df
    # Fill NaN and empty strings in integer columns with 0 before converting to int
    data_dict_df['Active'] = data_dict_df['Active'].replace('', '0').fillna('0')
    data_dict_df['form_sequence_id'] = data_dict_df['form_sequence_id'].replace('', '0').fillna('0')
    
    # Convert columns to appropriate types
    data_dict_df = data_dict_df.astype({
        'sequence': int, 
        'field_name': str, 
        'form_name': str, 
        'section_header': str, 
        'field_type': str, 
        'field_label': str, 
        'CreatedOn': 'datetime64[ns]', 
        'FileName': str, 
        'Active': int, 
        'form_sequence_id': int
    })
    
    # Select and rename columns as in the database table
    data_dict_df = data_dict_df[['sequence', 'form_name', 'field_name', 'section_header', 'field_label', 'field_type', 'FileName', 'CreatedOn', 'Active', 'form_sequence_id']]
    data_dict_df = data_dict_df.rename(columns={'sequence': 'SequenceId', 'field_name': 'FieldName', 'form_name': 'FormName', 
                                                'section_header': 'SectionHeader', 'field_type': 'FieldType', 'field_label': 'FieldLabel', 'Active': 'Active', 'form_sequence_id': 'FormSequenceId'})
    
    return data_dict_df