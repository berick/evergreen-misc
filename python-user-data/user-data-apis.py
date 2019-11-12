#!/usr/bin/python3
import sys, getopt, json
import urllib.parse as urlparser
import urllib.request as urlrequest

global api_url
global authtoken

def do_help(stat = 0):

    print (''' 
Usage:
    -u API URL [e.g. https://example.org/osrf-gateway-v1]

    -b barcode

    -p password
    
    ''')
    sys.exit(stat)

# Construct a JSON gateway API request and return the response as a 
# JSON thing.
def api_request(service, method, *params):

    post = urlparser.urlencode({'service': service, 'method': method})

    for p in params:
        post += '&param=%s' % urlparser.quote(json.dumps(p), "'/", 'UTF-8')

    post = post.encode('UTF-8')

    request = urlrequest.Request(api_url, data=post)
    response = urlrequest.urlopen(request)
    data = response.read()
    str_data = data.decode('UTF-8')

    print('\nAPI returned JSON:\n%s\n' % str_data)

    return json.loads(str_data)['payload']


# ------- start...

ops, args = None, None
try:
    ops, args = getopt.getopt(sys.argv[1:], 'u:b:p:h')
except getopt.GetoptError as e:
    print('* %s' % str(e))
    do_help(1)

options = dict(ops)

if '-b' not in options or '-p' not in options or '-u' not in options:
    do_help(1)

api_url = options['-u']
user_barcode = options['-b']
user_password = options['-p']

# Login
auth_response = api_request('open-ils.auth', 'open-ils.auth.login', 
    {'barcode': user_barcode, 'password': user_password, 'type': 'opac'});

authtoken = auth_response[0]['payload']['authtoken']

# Get basic user info from the authentication token
user_response = api_request(
    'open-ils.auth', 'open-ils.auth.session.retrieve', authtoken)

# XXX hard-coded object array indices (see fm_IDL.xml)
user_array = user_response[0]['__p']
user_id = user_array[28] 

print('\nUser ID: %d\n' % user_id)

# User checkout counts
checked_out_resp = api_request(
    'open-ils.actor', 'open-ils.actor.user.checked_out',
    authtoken, user_id)

print('\nCheckouts: \n%s\n' % json.dumps(checked_out_resp))

# Fines summary 
fines_response = api_request(
    'open-ils.actor', 'open-ils.actor.user.fines.summary',
    authtoken, user_id)

# XXX hard-coded object array indices (see fm_IDL.xml)
fines = fines_response[0]['__p']
print(
    '\nFines Summary: \nBalance Owed: $%0.2f, Total Owed $%0.2f, Total Paid $%0.2f\n'
    % (float(fines[0]), float(fines[1]), float(fines[2])))
    
# List of user holds
holds_resp = api_request('open-ils.circ', 
    'open-ils.circ.holds.retrieve', authtoken, user_id)




