#!/usr/bin/env python3

# Copyright 2010 University of Chicago
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Create Globus Endpoints from information registration
Based off of Transfer API example code.

python goendpoints.py USERNAME -k ~/.globus/userkey.pem -c ~/.globus/usercert.pem
"""
import time
import os
import re
from datetime import datetime, timedelta
import urllib3, json, ssl
url = "https://info.xsede.org/wh1/goendpoint-api/v1/goservices/"
import globus_sdk

#from globusonline.transfer.api_client import Transfer, create_client_from_args
from globus_sdk import TransferClient
from six.moves.configparser import (
    SafeConfigParser, MissingSectionHeaderError,
    NoOptionError, NoSectionError)

import django
django.setup()
from django.utils.dateparse import parse_datetime
from processing_status.process import ProcessingActivity

instdir = '/soft/warehouse-apps-1.0/Manage-GlobusEndpoints'
#instdir = '../'
#Get Auth Token
config = SafeConfigParser()
print(instdir+'/conf/goendpoints.cfg')
config.read(instdir+'/conf/goendpoints.cfg')
CLIENT_ID = config.get('Auth Options','CLIENT_ID')
CLIENT_SECRET = config.get('Auth Options','CLIENT_SECRET')
USERNAME = config.get('Auth Options','USERNAME')
PASSWORD = config.get('Auth Options','PASSWORD')
REFRESH_TOKEN = config.get('Auth Options','REFRESH_TOKEN')
XSEDE_SUBSCRIPTION_ID = 'a46ef5ed-6398-11e4-8dbc-22000b4213a5'
import http.client, urllib, ssl
#GRANT_TYPE = 'client_credentials'
GRANT_TYPE = 'password'
AUTH_OAUTH = "auth.globus.org"
SCOPES = {
      'urn:globus:auth:scope:auth.globus.org:view_identities': "Auth",
      'urn:globus:auth:scope:transfer.api.globus.org:all': "Transfer",
    };
SCOPESTRING = 'urn:globus:auth:scope:transfer.api.globus.org:all'

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

nac = globus_sdk.NativeAppAuthClient(CLIENT_ID)
nac.oauth2_start_flow(refresh_tokens=True)

print('Please go to this URL and login: {0}'
      .format(nac.oauth2_get_authorize_url()))

get_input = getattr(__builtins__, 'raw_input', input)
auth_code = get_input('Please enter the code here: ').strip()
token_response = nac.oauth2_exchange_code_for_tokens(auth_code)


print(token_response)

#authorizer = globus_sdk.RefreshTokenAuthorizer(
#    REFRESH_TOKEN, nac)

#client = TransferClient(authorizer=authorizer)
#print client

