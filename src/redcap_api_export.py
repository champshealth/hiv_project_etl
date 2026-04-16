# redcap_api_export.py
# this script will export the REDCap API data as a pandas dataframe
# IMPORTANT: Note that redcap api export is using flat format instead of eav format
# due to eav format returning no data possibly due to Data Access Group (DAG)
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import duckdb
import gc
from config.config import REDCAP_URL
from requests.exceptions import RequestException
from src.logging_config import logger

def _get_eav_columns(flat_df):
    """Helper to determine EAV output columns based on flat dataframe structure."""
    columns = ['record', 'field_name', 'value']
    has_repeat_instrument = 'redcap_repeat_instrument' in flat_df.columns
    has_repeat_instance = 'redcap_repeat_instance' in flat_df.columns
    has_site_id = 'site_id' in flat_df.columns
    
    if has_site_id:
        columns.insert(1, 'site_id')
    if has_repeat_instrument:
        idx = 1 if not has_site_id else 2
        columns.insert(idx, 'redcap_repeat_instrument')
    if has_repeat_instance:
        idx = 1
        if has_site_id:
            idx += 1
        if has_repeat_instrument:
            idx += 1
        columns.insert(idx, 'redcap_repeat_instance')
    
    return columns, has_site_id, has_repeat_instrument, has_repeat_instance


def _process_chunk_with_duckdb(chunk_df, record_id_col, columns, has_site_id, has_repeat_instrument, has_repeat_instance):
    """Process a single chunk using DuckDB for memory-efficient EAV transformation."""
    conn = duckdb.connect()
    try:
        # Register the chunk as a temporary table
        conn.execute("CREATE TEMPORARY TABLE chunk_df AS SELECT * FROM chunk_df")
        
        # Build UNPIVOT query dynamically based on available columns
        id_cols = [f'"{record_id_col}" AS record']
        if has_site_id:
            id_cols.append('"site_id"')
        if has_repeat_instrument:
            id_cols.append('redcap_repeat_instrument')
        if has_repeat_instance:
            id_cols.append('redcap_repeat_instance')
        
        id_cols_str = ', '.join(id_cols)
        
        # Get all field columns (exclude id columns)
        exclude_cols = [record_id_col, 'site_id', 'redcap_repeat_instrument', 'redcap_repeat_instance']
        field_cols = [c for c in chunk_df.columns if c not in exclude_cols]
        
        # Build UNPIVOT query
        field_cols_quoted = ', '.join([f'"{c}"' for c in field_cols])
        
        unpivot_query = f"""
            SELECT 
                {id_cols_str},
                field_name,
                value::VARCHAR as value
            FROM chunk_df
            UNPIVOT (
                value FOR field_name IN ({field_cols_quoted})
            )
            WHERE value IS NOT NULL AND TRIM(value::VARCHAR) != ''
        """
        
        eav_df = conn.execute(unpivot_query).fetchdf()
        
        # Handle checkbox fields
        if not eav_df.empty:
            checkbox_mask = eav_df['field_name'].str.contains('___', na=False)
            if checkbox_mask.any():
                checkbox_rows = eav_df[checkbox_mask].copy()
                non_checkbox_rows = eav_df[~checkbox_mask]
                
                # Extract code from field name when value is 1
                checkbox_rows.loc[checkbox_rows['value'] == '1', 'value'] = \
                    checkbox_rows.loc[checkbox_rows['value'] == '1', 'field_name'].str.extract(r'___(.+)$')[0]
                
                # Remove ___code from field names
                checkbox_rows['field_name'] = checkbox_rows['field_name'].str.replace(r'___.*$', '', regex=True)
                
                # Filter out rows where value is 0
                checkbox_rows = checkbox_rows[checkbox_rows['value'] != '0']
                
                # Combine
                eav_df = pd.concat([non_checkbox_rows, checkbox_rows], ignore_index=True)
        
        # Ensure proper column order
        eav_df = eav_df[columns]
        
        # Convert all to string
        for col in eav_df.columns:
            eav_df[col] = eav_df[col].astype(str)
        
        return eav_df
    finally:
        conn.close()


def convert_flat_to_eav(flat_df, chunk_size=5000):
    """
    Convert flat dataframe to EAV format with checkbox field handling.
    Uses chunked processing with DuckDB for memory efficiency.
    
    Args:
        flat_df: Input dataframe in flat format
        chunk_size: Number of rows to process per chunk (default 5000)
    
    Returns:
        DataFrame in EAV format
    """
    if flat_df.empty:
        return pd.DataFrame(columns=['record', 'field_name', 'value'])
    
    # Get record identifier column
    record_id_col = flat_df.columns[0]
    
    # Determine output columns
    columns, has_site_id, has_repeat_instrument, has_repeat_instance = _get_eav_columns(flat_df)
    
    total_rows = len(flat_df)
    
    # For small datasets, process directly
    if total_rows <= chunk_size:
        return _process_chunk_with_duckdb(
            flat_df, record_id_col, columns, 
            has_site_id, has_repeat_instrument, has_repeat_instance
        )
    
    # Process in chunks for large datasets
    logger.info(f"Processing {total_rows} rows in chunks of {chunk_size} for EAV conversion")
    results = []
    num_chunks = (total_rows + chunk_size - 1) // chunk_size
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, total_rows)
        chunk = flat_df.iloc[start_idx:end_idx].copy()
        
        logger.info(f"Processing chunk {i+1}/{num_chunks} (rows {start_idx}-{end_idx})")
        
        result = _process_chunk_with_duckdb(
            chunk, record_id_col, columns,
            has_site_id, has_repeat_instrument, has_repeat_instance
        )
        results.append(result)
        
        # Clear memory
        del chunk
        gc.collect()
    
    # Combine all results
    final_df = pd.concat(results, ignore_index=True)
    
    # Sort by record and field_name
    final_df = final_df.sort_values(['record', 'field_name']).reset_index(drop=True)
    
    logger.info(f"Completed EAV conversion: {len(final_df)} rows from {total_rows} flat rows")
    return final_df

def redcap_api_export(redcap_tokens: list, output_file) -> pd.DataFrame:
    """
    Export the REDCap API data as a pandas dataframe.
    
    Args:
        redcap_tokens: List of dictionaries containing token metadata
        output_file: Path for output files
    """
    # Flatten the tokens list if it's nested
    if redcap_tokens and isinstance(redcap_tokens[0], list):
        redcap_tokens = [token for sublist in redcap_tokens for token in sublist]

    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    
    # Update the session configuration
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    # Add timeouts
    session.timeout = (5, 30)  # (connect timeout, read timeout)

    all_dfs = []
    skip_projects = []
    
    for token_info in redcap_tokens:
        project_name = token_info['name']
        
        # Skip projects that are known to have issues
        if project_name in skip_projects:
            logger.warning(f"Skipping known problematic project: {project_name}")
            continue
            
        logger.info(f"Fetching data for project: {project_name}")
        data = {
            'token': str(token_info['token']),
            'content': 'record',
            'action': 'export',
            'format': 'json',
            'type': 'flat',
            'rawOrLabel': 'raw',
            'rawOrLabelHeaders': 'raw',
            'exportCheckboxLabel': 'true',
            'exportSurveyFields': 'false',
            'exportDataAccessGroups': 'false',
            'returnFormat': 'json'
        }

        try:
            response = session.post(REDCAP_URL, data=data)
            response.raise_for_status()

            json_data = response.json()
            if json_data:
                # Convert all values to strings to preserve leading zeros and prevent numeric conversion
                for record in json_data:
                    for key, value in record.items():
                        if value is not None:
                            record[key] = str(value)
                            
                df = pd.DataFrame(json_data)
                if 'site_id' in df.columns:
                    print("Site ID column found for project:", project_name)
                # Temporary workaround for South Africa project - set site_id to "001"
                if output_file.endswith("redcap_export_11"):
                    if project_name == "south_africa":
                        # Ensure site_id column exists
                        if 'site_id' not in df.columns:
                            df['site_id'] = "001"
                        else:
                            # Set all site_id values to "001"
                            df['site_id'] = "001"
                        logger.info(f"Applied site_id workaround for project: {project_name}")
                
                # write to csv for debugging
                # print(f"Writing flat data to CSV for project {project_name}")
                # df.to_csv(f"data/redcap_{project_name}_flat.csv", index=False)

                # Convert flat dataframe to EAV format
                df = convert_flat_to_eav(df)
                # df['redcap_project'] = project_name
                all_dfs.append(df)
                logger.info(f"Successfully processed data for {project_name} with {len(df)} rows")
            else:
                logger.warning(f"No data returned for project: {project_name}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from REDCap API for project {project_name}: {e}")

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        
        # Convert redcap_repeat_instance to string before writing
        if 'redcap_repeat_instance' in final_df.columns:
            final_df['redcap_repeat_instance'] = final_df['redcap_repeat_instance'].astype(str)
        
        final_df.to_csv(output_file + ".csv", index=False)
        try:
            final_df.to_parquet(output_file + ".parquet", index=False)
        except Exception as e:
            logger.warning(f"Error writing parquet file: {e}")
        
        return final_df
    
    return None