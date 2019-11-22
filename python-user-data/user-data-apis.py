#!/usr/bin/python3
import sys, getopt, json
import urllib.parse as urlparser
import urllib.request as urlrequest

global api_url
global authtoken

# Bib record ID
hold_target = 137229

hold_pickup_lib = 1533 # RE

# ID for hold linked to this script's login account
hold_details_id = 58001146

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

vital_stats_resp = api_request('open-ils.actor',
    'open-ils.actor.user.opac.vital_stats', authtoken, user_id)

vital_stats = vital_stats_resp[0]

print('User has %d holds ready' % vital_stats['holds']['ready'])

# List of user holds
holds_resp = api_request('open-ils.circ', 
    'open-ils.circ.holds.retrieve', authtoken, user_id)

create_hold_resp = api_request('open-ils.circ',
    'open-ils.circ.holds.test_and_create.batch', authtoken, {
        'hold_type': 'T',
        'patronid': user_id,
        'pickup_lib': hold_pickup_lib
    }, 
    [hold_target])

# Details for one hold by ID.
# Note the hold must be linked to the same account used by this script
hold_details_resp = api_request('open-ils.circ',
    'open-ils.circ.hold.details.retrieve', 
    authtoken, hold_details_id)


