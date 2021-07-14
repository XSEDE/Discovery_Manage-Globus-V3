#!/bin/bash
MY_BASE=/soft/warehouse-apps-1.0/Manage-GlobusEndpoints
PYTHON_BASE=/soft/python/python-3.8.11-base
export LD_LIBRARY_PATH=${PYTHON_BASE}/lib
PYTHON_ROOT=/soft/warehouse-apps-1.0/Manage-GlobusEndpoints/python
source ${PYTHON_ROOT}/bin/activate
PYTHON_BIN=python3

CONTACTS="blau@mcs.anl.gov"
PYTHONPATH=/soft/warehouse-1.0/PROD/django_xsede_warehouse:$PYTHONPATH
PYTHONPATH=${MY_BASE}/python/lib/python3.6/site-packages/:$PYTHONPATH
export PYTHONPATH
export PYTHONUSERBASE=${MY_BASE}/local/pythonuserbase
export PYTHONIOENCODING=utf8
export DJANGO_CONF=/soft/warehouse-apps-1.0/Manage-GlobusEndpoints/conf/django_xsede_warehouse.conf
export DJANGO_SETTINGS_MODULE=xsede_warehouse.settings

${PYTHON_BIN} ${MY_BASE}/PROD/sbin/bootstrap_token.py
