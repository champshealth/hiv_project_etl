#!/usr/bin/env python3
"""
Test script for HIV Project 1.1 data pipeline.

This script:
1. Fetches data from vw_HIVProject1_1 view
2. Pivots the data using DuckDB
3. Saves the output to a CSV file in the data directory
"""
import os
import pandas as pd
from datetime import datetime
from src.labkey_load_project_1_1 import get_hiv_project1_1_data, pivot_hiv_project1_1_data
from src.logging_config import logger

def main():
    try:
        # Ensure output directory exists
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"hiv_project1_1_pivoted_{timestamp}.csv")
        
        logger.info("Starting HIV Project 1.1 data pipeline")
        
        # Step 1: Get the data
        logger.info("Fetching data from vw_HIVProject1_1...")
        df = get_hiv_project1_1_data()
        logger.info(f"Retrieved {len(df)} rows of data")
        
        # Step 2: Pivot the data
        logger.info("Pivoting data...")
        pivoted_df = pivot_hiv_project1_1_data(df)
        logger.info(f"Pivoted data has {len(pivoted_df)} rows and {len(pivoted_df.columns)} columns")
        
        # Step 3: Save to CSV
        pivoted_df.to_csv(output_file, index=False)
        logger.info(f"Saved pivoted data to {output_file}")
        
        # Print some basic info
        print("\nPipeline completed successfully!")
        print(f"Original rows: {len(df)}")
        print(f"Pivoted rows: {len(pivoted_df)}")
        print(f"Pivoted columns: {len(pivoted_df.columns)}")
        print(f"Output file: {os.path.abspath(output_file)}")
        
    except Exception as e:
        logger.error(f"Error in HIV Project 1.1 pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()
