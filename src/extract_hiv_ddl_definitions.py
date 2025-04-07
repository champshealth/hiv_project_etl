import pandas as pd
import sqlalchemy as sa
from config.config import CONN
from src.logging_config import logger
import datetime

def extract_hiv_table_ddl_definitions():
    try:
        sql = """
        SELECT 
            SCHEMA_NAME(t.schema_id) as schema_name,
            t.name as table_name,
            'CREATE TABLE [' + SCHEMA_NAME(t.schema_id) + '].[' + t.name + '] (' + CHAR(13) +
            STUFF((
                SELECT CHAR(13) + '    [' + c.name + '] [' + 
                    tp.name + ']' + 
                    CASE 
                        WHEN tp.name IN ('varchar', 'nvarchar', 'char', 'nchar') 
                            THEN '(' + CASE WHEN c.max_length = -1 THEN 'max' 
                                          ELSE CAST(c.max_length AS VARCHAR(10)) END + ')'
                        WHEN tp.name IN ('decimal', 'numeric') 
                            THEN '(' + CAST(c.precision AS VARCHAR(10)) + ',' + CAST(c.scale AS VARCHAR(10)) + ')'
                        ELSE ''
                    END + ' ' +
                    CASE WHEN c.is_nullable = 1 THEN 'NULL' ELSE 'NOT NULL' END + ','
                FROM sys.columns c
                INNER JOIN sys.types tp ON c.user_type_id = tp.user_type_id
                WHERE c.object_id = t.object_id
                ORDER BY c.column_id
                FOR XML PATH(''), TYPE).value('.', 'VARCHAR(MAX)'), 1, 0, '') + CHAR(13) + 
            ') ON [PRIMARY]' +
            CASE WHEN EXISTS (
                SELECT 1 FROM sys.columns c
                JOIN sys.types tp ON c.user_type_id = tp.user_type_id
                WHERE c.object_id = t.object_id 
                AND tp.name IN ('varchar', 'nvarchar', 'text', 'ntext')
                AND c.max_length = -1
            ) THEN ' TEXTIMAGE_ON [PRIMARY]' ELSE '' END as ddl_definition
        FROM sys.tables t
        WHERE t.name LIKE '%HIV%'
        ORDER BY schema_name, table_name;
        """

        with CONN.connect() as conn:
            df = pd.read_sql(sql, conn)
            
            output_dir = 'data/ddl_definitions'
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            for _, row in df.iterrows():
                filename = f"{row['schema_name']}.{row['table_name']}.sql"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w') as f:
                    f.write(f"-- Schema: {row['schema_name']}\n")
                    f.write(f"-- Table: {row['table_name']}\n")
                    f.write(f"-- Generated: {datetime.datetime.now()}\n\n")
                    f.write(row['ddl_definition'])
                    
            logger.info(f"Generated {len(df)} table definitions")
            logger.info(f"Saved DDL files to {output_dir}")
            
            return df

    except Exception as e:
        logger.error(f"Error generating table definitions: {e}")
        raise

def extract_hiv_view_ddl_definitions():
    """Extract DDL definitions for tables/views containing 'HIV' in their name."""
    try:
        # SQL query to get DDL definitions with fallback for NULL definitions
        sql = """
        SELECT 
            OBJECT_SCHEMA_NAME(o.object_id) AS schema_name,
            o.name AS object_name,
            o.type_desc AS object_type,
            COALESCE(OBJECT_DEFINITION(o.object_id), 
                     '-- No definition available for this object') AS ddl_definition
        FROM sys.objects o
        WHERE o.name LIKE '%HIV%'
        AND o.type IN ( 'V')  -- U for Tables, V for Views
        ORDER BY o.type_desc, schema_name, o.name;
        """

        with CONN.connect() as conn:
            # Get definitions
            df = pd.read_sql(sql, conn)
            
            if df.empty:
                logger.warning("No HIV tables or views found")
                return df
                
            # Save DDL to individual .sql files
            output_dir = 'src/ddl_definitions'
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            for _, row in df.iterrows():
                try:
                    filename = f"{row['schema_name']}.{row['object_name']}.sql"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'w') as f:
                        f.write(f"-- {row['object_type']}\n")
                        f.write(f"-- Schema: {row['schema_name']}\n")
                        f.write(f"-- Name: {row['object_name']}\n")
                        f.write(f"-- Generated: {datetime.datetime.now()}\n\n")
                        f.write(str(row['ddl_definition']))
                        
                except Exception as e:
                    logger.error(f"Error writing {filename}: {str(e)}")
                    continue
                    
            logger.info(f"Extracted {len(df)} DDL definitions")
            logger.info(f"Saved DDL files to {output_dir}")
            
            # Print summary
            summary = df.groupby(['schema_name', 'object_type']).size()
            logger.info("\nObjects extracted:")
            logger.info(summary)
            
            return df

    except Exception as e:
        logger.error(f"Error extracting DDL definitions: {e}")
        raise

if __name__ == "__main__":
    extract_hiv_table_ddl_definitions()