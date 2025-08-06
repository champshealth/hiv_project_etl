#!/bin/bash
# setup the python 3.9 env from /opt/jobs/miniconda3 
# only used from the cron job on the server cmpjobprod1
. /opt/jobs/scripts/scripts_py39.env
# activate venv
source /opt/jobs/scripts/hiv_project_etl/venv/bin/activate
# echo which python
echo `which python`
TODAY=`date +%Y_%m_%d_%H_%M_%S`
FILE_NAME=`echo $1|cut -d '.' -f 1`
if [ "$1" != "" ]; then
#    echo "Running script $1 " 
    cd $SCRIPT_DIR/hiv_project_etl/
    python $SCRIPT_DIR/hiv_project_etl/$1 > $LOG_DIR/run_py39_script_cron_${FILE_NAME}_$TODAY.log 2>&1 
else
    echo "argv[1] parameter 1 is empty. argv[1] should be a python script to be executed "
fi