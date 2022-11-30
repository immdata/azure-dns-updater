from azure.identity import ClientSecretCredential
from azure.mgmt.dns import DnsManagementClient
from requests import get
from socket import gethostbyname
import time
import os
import sys


def definevar(var: str, cast: type) -> str:
    if var in os.environ:
        return os.environ[var]
    else:
        args = sys.argv[1:]
        for arg in args:
            arg_clean = arg.replace('--', '', 1).split('=')
            if arg_clean[0] == var:
                return cast(arg_clean[1])
    return


TENANT_ID = definevar('TENANT_ID', str)
APP_ID = definevar('APP_ID', str)
APP_SECRET = definevar('APP_SECRET', str)
SUBSCRIPTION_ID = definevar('SUBSCRIPTION_ID', str)
RESOURCE_GROUP = definevar('RESOURCE_GROUP', str)
RECORD_SET = definevar('RECORD_SET', str)
DOMAIN = definevar('DOMAIN', str)
interval = definevar('INTERVAL', int)
INTERVAL = 300 if interval is None else int(interval)

headers = {
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Connection": "close"
}

credentials = ClientSecretCredential(
    tenant_id=TENANT_ID,
    client_id=APP_ID,
    client_secret=APP_SECRET
)

dns_client = DnsManagementClient(
    credentials,
    SUBSCRIPTION_ID
)

while True:
    try:
        sys.stderr.write(f'[{time.strftime("%H:%M:%S")}]\n')
        public_ip = get('https://api.ipify.org', headers=headers).text
        sys.stderr.write(f'Public IP address: {public_ip}.\n')

        for record_set in RECORD_SET.split(','):
            sys.stderr.write(f'Checking {record_set} record set...\n')
            host = ('a.' if record_set == '*' else ('' if record_set ==
                                                    '@' else record_set + ".")) + DOMAIN
            current_ip = gethostbyname(host)
            sys.stderr.write(f'Current IP address for record: {current_ip}.\n')

            if public_ip == current_ip:
                sys.stderr.write('No change.\n')
            else:
                dns_client.record_sets.create_or_update(
                    RESOURCE_GROUP,
                    DOMAIN,
                    record_set,
                    'A',
                    {
                        "ttl": INTERVAL,
                        "arecords": [
                            {
                                "ipv4_address": public_ip
                            }
                        ]
                    }
                )
                sys.stderr.write(f'Record {record_set} changed.')
    except Exception as ex:
        sys.stderr.write(f'ERROR: ')
        print(ex, file=sys.stderr)

    sys.stderr.write('\n\n')
    time.sleep(INTERVAL)
