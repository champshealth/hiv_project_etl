import os
import configparser
from pathlib import Path

local_creds_file = os.path.join(str(Path.home()),'.config','local_credentials')
config = configparser.ConfigParser()
config.read(local_creds_file)
db_pwd = config['MSSQL']['MSSQL_SCRIPTER_PASSWORD']


# tableau server credentials
# tab_server = config['tableau']['server']
# tab_site = config['tableau']['site']
# tab_user = config['tableau']['userid']
# tab_pwd = config['tableau']['password']

class connect_db():
    from sqlalchemy import create_engine
    dsn = 'champs_qa'
    username = 'champs_measure'
    password = db_pwd
    ss_driver = 'ODBC Driver 18 for SQL Server'
    
    conn_qa = create_engine(f'mssql+pyodbc://{username}:{password}@{dsn}')

# class connect_db():
#     # CHAMPS SQL Sever  database connections.
#     import sqlalchemy
#     import os
#     # ss_driver = 'driver=ODBC+Driver+17+for+SQL+Server'
#     ss_driver = 'driver=ODBC+Driver+18+for+SQL+Server'
#     conn_prod_rpt = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqlprd101/champs_prod_reporting?' + ss_driver)
#     conn_qa_rpt = sqlalchemy.create_engine(
#         "mssql+pyodbc://champs_measure:" + db_pwd + "@cmpsqldev101/champs_qa_reporting?" + ss_driver)
#     conn_prod = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqlprd101/champs_prod?' + ss_driver)
#     conn_prod_aux = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqlprd101/champs_auxiliary?' + ss_driver)
#     conn_dev = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqldev101/champs_dev?' + ss_driver)
#     conn_stg = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqldev101/champs_stg?' + ss_driver)
#     conn_stg_rpt = sqlalchemy.create_engine(
#         "mssql+pyodbc://champs_measure:" + db_pwd + "@cmpsqldev101/champs_stg_reporting?" + ss_driver)
#     conn_dev_aux = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqldev101/champs_auxiliary?' + ss_driver)
#     conn_qa = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqldev101/champs_qa?' + ss_driver)
#     conn_qa_aux = sqlalchemy.create_engine(
#         'mssql+pyodbc://champs_measure:' + db_pwd + '@cmpsqldev101/champs_auxiliary?' + ss_driver)



