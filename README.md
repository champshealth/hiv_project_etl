### HIV project data pipeline
This project is a data pipeline that processes data from the HIV project. This project pulls data from the REDCAP HIV projects and stores it in sqlserver. The data os then pulled into Tableau reports for Decode Reports and into labkey.

directory tree:
src/ - contains the source code for the project
data/ - contains the data for the project
logs/ - contains the logs for the project
config/ - contains the configuration files for the project
include/ - contains the include files for the project

<!-- Database objects deployment -->
- [ ] Generate the db object definitions using the `create_ddl.py` script
- [ ] Create database objects using the ddl files in the `src/ddl_definitions` directory
- [ ] load the Tableau report definitions from the `rpt_HIVReportName.csv` file