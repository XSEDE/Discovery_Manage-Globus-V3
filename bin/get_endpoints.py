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
import globus_sdk
from datetime import datetime, timedelta
import urllib3, json, ssl
url = "https://info.xsede.org/wh1/goendpoint-api/v1/goservices/"

#from globusonline.transfer.api_client import Transfer, create_client_from_args
from globus_sdk import TransferClient
from six.moves.configparser import (
    SafeConfigParser, MissingSectionHeaderError,
    NoOptionError, NoSectionError)

import django
django.setup()
#from django.utils.dateparse import parse_datetime
from processing_status.process import ProcessingActivity

instdir = '/soft/warehouse-apps-1.0/Manage-Globus-v3'
#instdir = '../'
#Get Auth Token
config = SafeConfigParser()
config.read(instdir+'/conf/goendpoints.cfg')
CLIENT_ID = config.get('Auth Options','CLIENT_ID')
CLIENT_SECRET = config.get('Auth Options','CLIENT_SECRET')
USERNAME = config.get('Auth Options','USERNAME')
PASSWORD = config.get('Auth Options','PASSWORD')
REFRESH_TOKEN = config.get('Auth Options','REFRESH_TOKEN')
EXTRA_ENDPOINTS_FILE = config.get('XSEDE Options','ENDPOINT_LIST')
XSEDE_SUBSCRIPTION_ID = config.get('XSEDE Options','XSEDE_SUBSCRIPTION_ID')
#XSEDE_SUBSCRIPTION_ID = 'a46ef5ed-6398-11e4-8dbc-22000b4213a5'
import http.client, urllib, ssl

AUTH_OAUTH = "auth.globus.org"
SCOPES = {
      'urn:globus:auth:scope:auth.globus.org:view_identities': "Auth",
      'urn:globus:auth:scope:transfer.api.globus.org:all': "Transfer",
    };
SCOPESTRING = 'urn:globus:auth:scope:transfer.api.globus.org:all'

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

nac = globus_sdk.NativeAppAuthClient(CLIENT_ID)

ls

authorizer = globus_sdk.RefreshTokenAuthorizer(
    REFRESH_TOKEN, nac)

client = TransferClient(authorizer=authorizer)



def main():
    #context = ssl.create_default_context(cafile="info_cacerts.pem")
    context = ssl._create_unverified_context()
    #response = urllib3.urlopen(url, cafile="info_cacerts.pem")
    #response = urllib3.urlopen(url, context=context)
    response = urllib.request.urlopen(url, context=context)
    data = json.loads(response.read())
    published_endpoints = {}
    endpoint_list = client.endpoint_search(filter_scope='my-endpoints',num_results=120)
    differences={}
    for endpoint in data:
        print(endpoint['URL'])
        published_endpoints["xsede#"+generate_endpoint_name(endpoint)+endpoint['URL'].rstrip('/')]=endpoint

    #code, reason, endpoint_list = api.endpoint_list(limit=100,filter='username:'+api.username)

    with open('EXTRA_ENDPOINTS_FILE') as f:
    extra_endpoints = f.read().splitlines()

    existing_endpoints = {}
    #for ep in endpoint_list["DATA"]:
    for ep in endpoint_list.data:
        serverlist = client.endpoint_server_list(ep['id'])
        for serverdata in serverlist:
            if serverdata['uri']:
                existing_endpoints[ep['canonical_name']+serverdata['uri']] = ep
    print("Existing Endpoints:")
    for key in existing_endpoints:
        print(key)

    for pubendpoint in published_endpoints:
        name =  generate_endpoint_name(published_endpoints[pubendpoint])
        hostname,port = published_endpoints[pubendpoint]['URL'].replace('gsiftp://','').split(":")
        port = port.replace('/','')
        #hostname = published_endpoints[puburl]['DATA'][0]['hostname']
        #port = published_endpoints[puburl]['DATA'][0]['port']
        puborg=""
        puborgabbr=""
        rdrdesc=""
        enddesc=""
        pubkeywords=""
        if published_endpoints[pubendpoint]['RDR_Fields']:
            rdrdesc = published_endpoints[pubendpoint]['RDR_Fields']['RDR_Description']
            puborg = published_endpoints[pubendpoint]['RDR_Fields']['Organization_Name']
            puborgabbr = published_endpoints[pubendpoint]['RDR_Fields']['Organization_Abbreviation']
            pubkeywords = "XSEDE, "+published_endpoints[pubendpoint]['RDR_Fields']['Organization_Abbreviation']+", "+name
        enddesc = published_endpoints[pubendpoint]['Description']
        enddisp = published_endpoints[pubendpoint]['DisplayName']
        #enddisp = "XSEDE "+puborgabbr+" "+name
        data=create_endpoint_data(endpoint_name=name,description=enddesc or rdrdesc, hostname=hostname, port=port, organization=puborg, keywords=pubkeywords or ("XSEDE" + (" ," + puborgabbr if puborgabbr else "") +" ,"+name), display_name=enddisp or ("XSEDE" + (" " + puborgabbr or "") +" "+name))
        process_status_for_published_endpoint(published_endpoints[pubendpoint])

        if not pubendpoint in existing_endpoints:
            print("need to create endpoint for %s", pubendpoint)
            print(name, hostname, port)
            create_endpoint(data)
            
        else:
            print("need to compare endpoints for %s", pubendpoint)
            diff={}
            for field in data:
                #p = re.compile(r'^(?:[\'"])(?P<string>.*?)(?:[\'"])$')
                if field == 'DATA':
                    continue
                m = re.match(r'^(?:[\'"])(?P<string>.*?)(?:[\'"])$',str(existing_endpoints[pubendpoint][field]))
                if m is not None:
                    teststring = m.group('string')
                else:
                    teststring = existing_endpoints[pubendpoint][field]
                #if data[field] != existing_endpoints[puburl][field]:
                if data[field] != teststring:
                    diff[field]=""
                    diffs={}
                    print("Field %s published as %s but is registered as %s" % ( field, data[field], existing_endpoints[pubendpoint][field]))
                    diffs["Published"]=data[field]
                    diffs["Registered"]=existing_endpoints[pubendpoint][field]
                    diff[field]=diffs
                    differences[pubendpoint]=diff

    #print(differences)
    timestamp = '{:%Y-%m-%d-%H:%M:%S}'.format(datetime.now())
    tsfile = instdir+"/var/"+"EndpointDiff-"+timestamp+".json"
    with open(tsfile, 'w') as timestampfile:
        json.dump(differences, timestampfile)
        os.system("ln -s "+instdir+"/var/"+"EndpointDiff-"+timestamp+".json "+instdir+"/var/"+"Newest.json")
    return

def generate_endpoint_name(endpoint):
    print("ResourceID is %s \n", endpoint['ResourceID'])
    first,second,rest = endpoint['ResourceID'].split(".",2)
    if first == "hpss":
        return first+"-"+second
    if first == "wrangler":
        if second == "iu":
            return first+"-"+second
    return first



def display_endpoint_list():
    code, reason, endpoint_list = api.endpoint_list(limit=100)
    print("Found %d endpoints for user %s:" \
          % (endpoint_list["length"], api.username))
    for ep in endpoint_list["DATA"]:
        _print_endpoint(ep)


def display_endpoint(endpoint_name):
    code, reason, data = api.endpoint(endpoint_name)
    _print_endpoint(data)


def _print_endpoint(ep):
    name = ep["canonical_name"]
    print(name)
    if ep["activated"]:
        print("  activated (expires: %s)" % ep["expire_time"])
    else:
        print("  not activated")
    if ep["public"]:
        print("  public")
    else:
        print("  not public")
    if ep["myproxy_server"]:
        print("  default myproxy server: %s" % ep["myproxy_server"])
    else:
        print("  no default myproxy server")
    servers = ep.get("DATA", ())
    print("  servers:")
    for s in servers:
        uri = s["uri"]
        if not uri:
            uri = "GC endpoint, no uri available"
        print("    " + uri,)
        if s["subject"]:
            print(" (%s)" % s["subject"])
        else:
            print()

def create_endpoint_data(endpoint_name, hostname=None, description="",
                        scheme="gsiftp", port=2811, subject=None,
                        myproxy_server="myproxy.xsede.org", myproxy_dn=None,
                        public=True, is_globus_connect=False,
                        default_directory=None, oauth_server="oa4mp.xsede.org",
                        organization="", display_name="", 
                        contact_email="help@xsede.org", keywords="", 
                        ):

        #@return: (status_code, status_reason, data)
        #@raise TransferAPIError

        data = { "DATA_TYPE": "endpoint",
                 #"myproxy_server": "myproxy.xsede.org",
                 "description": description,
                 #"canonical_name": api.username+"#"+endpoint_name,
                 "canonical_name": "xsede#"+endpoint_name,
                 "display_name": display_name or endpoint_name ,
                 "organization": organization,
                 "keywords": keywords,
                 "contact_email": "help@xsede.org",
                 "public": public,
                 "is_globus_connect": is_globus_connect,
                 "default_directory": default_directory,
                 "oauth_server": oauth_server,
                 "subscription_id": XSEDE_SUBSCRIPTION_ID, }
        if not is_globus_connect:
            data["DATA"] = [dict(DATA_TYPE="server",
                                 hostname=hostname,
                                 scheme=scheme,
                                 port=port,
                                 subject=subject)]
        print(json.dumps(data))
        return data

def create_endpoint(data):
        print(json.dumps(data))
        print(data)
        #return api.post("/endpoint", json.dumps(data))
        #return client.create_endpoint(json.dumps(data))
        return client.create_endpoint(data)

def process_status_for_published_endpoint(pubendpoint):
        pa_application=os.path.basename(__file__)
        pa_function='main'
        pa_topic = 'GoEndpoints'
        pa_id = pubendpoint['ID']
        pa_about = pubendpoint['ResourceID']
        pa = ProcessingActivity(pa_application, pa_function, pa_id , pa_topic, pa_about)
        pa.FinishActivity(0, "")
        return

if __name__ == '__main__':
    #api, _ = create_client_from_args()
    main()
