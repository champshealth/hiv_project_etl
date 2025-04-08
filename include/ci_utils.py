import os
import configparser
from pathlib import Path
import sqlalchemy

local_creds_file = os.path.join(str(Path.home()),'.config','local_credentials')
config = configparser.ConfigParser()
config.read(local_creds_file)
db_pwd = config['MSSQL']['MSSQL_SCRIPTER_PASSWORD']

class connect_db():
    # CHAMPS SQL Sever database connections.
    
    # Connection parameters
    driver_path = '/opt/homebrew/Cellar/msodbcsql18/18.4.1.1/lib/libmsodbcsql.18.dylib'
    username = 'champs_measure'
    password = db_pwd
    
    # Server endpoints
    prod_server = 'cmpsqlprd101.cc.emory.edu'
    dev_server = 'cmpsqldev101.cc.emory.edu'
    
    # Common database names
    db_prod = 'champs_prod'
    db_prod_rpt = 'champs_prod_reporting'
    db_qa = 'champs_qa'
    db_qa_rpt = 'champs_qa_reporting'
    db_dev = 'champs_dev'
    db_stg = 'champs_stg'
    db_stg_rpt = 'champs_stg_reporting'
    db_aux = 'champs_auxiliary'
    
    # The correct format for SQLAlchemy + pyodbc connection string on macOS
    conn_string_template = (
        "mssql+pyodbc://{username}:{password}@{server}/{database}?"
        "driver={driver}&TrustServerCertificate=yes&Encrypt=yes"
    )
    
    # Helper method to create connection engines
    @classmethod
    def create_connection(cls, server, database):
        return sqlalchemy.create_engine(
            cls.conn_string_template.format(
                username=cls.username,
                password=cls.password,
                server=server,
                database=database,
                driver=cls.driver_path
            )
        )
    
    # Production connections
    conn_prod_rpt = property(lambda cls: cls.create_connection(cls.prod_server, cls.db_prod_rpt))
    conn_prod = property(lambda cls: cls.create_connection(cls.prod_server, cls.db_prod))
    conn_prod_aux = property(lambda cls: cls.create_connection(cls.prod_server, cls.db_aux))
    
    # QA connections
    conn_qa_rpt = property(lambda cls: cls.create_connection(cls.dev_server, cls.db_qa_rpt))
    conn_qa = property(lambda cls: cls.create_connection(cls.dev_server, cls.db_qa))
    conn_qa_aux = property(lambda cls: cls.create_connection(cls.dev_server, cls.db_aux))
    
    # Development connections
    conn_dev = property(lambda cls: cls.create_connection(cls.dev_server, cls.db_dev))
    conn_dev_aux = property(lambda cls: cls.create_connection(cls.dev_server, cls.db_aux))
    
    # Staging connections
    conn_stg = property(lambda cls: cls.create_connection(cls.dev_server, cls.db_stg))
    conn_stg_rpt = property(lambda cls: cls.create_connection(cls.dev_server, cls.db_stg_rpt))