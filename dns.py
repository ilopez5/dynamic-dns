#!/bin/python3
from datetime import datetime as dt
from requests import get, patch
from socket   import gethostbyname
from getopt   import getopt, GetoptError
from json     import loads
from os       import getenv, path
import sys

# globals
domain  = ''
logFile = ''
errFile = ''

headers = {
    'X-Auth-Email': getenv('CF_EMAIL'),
    'X-Auth-Key'  : getenv('CF_TOKEN'),
    'Content-Type': 'application/json',
}

# collects program arguments
def parse():
    global domain, logFile, errFile
    try:
        opts, args = getopt(sys.argv[1:], 'hd:o:e:', ['help', 'output=', 'error='])
    except GetoptError as err:
        usage(code=1, message=err)

    for opt, arg in opts:
        if   opt in ('-h', '--help'):
            usage()
        elif opt in ('-d', '--domain'):
            domain  = arg
        elif opt in ('-o', '--output'):
            logFile = arg
        elif opt in ('-e', '--error'):
            errFile = arg
        else:
            usage(code=2, message=f'Unhandled option {opt}')
    # verification and log clean up
    if not domain:
        usage(code=3, message=f'Must provide a valid domain!')
    elif not all(headers.values()):
        usage(code=4, message=f'CF_EMAIL and/or CF_TOKEN environment variables not set!')
    elif not logFile:
        logFile = f"{domain.split('.')[0]}.dns.change.log"
    elif not errFile:
        errFile = f"{domain.split('.')[0]}.dns.error.log"
    return

def usage(code=0, message=''):
    file_name = path.basename(__file__)
    print(f'{message}\n'
          f'Usage: python3 {file_name} [-d example.com] [OPTIONS]\n'
            '\t-d, --domain\tTop-Level Domain (DNS managed by Cloudflare)\n'
            '\t-o, --output\tOutput log file\n'
            '\t-e, --error\tError file.')
    sys.exit(code)

def getLocalIP():
    return get('https://api.ipify.org').text

def getPublicIP():
    return gethostbyname(domain)

def getZone():
    global domain
    # ping to get zone
    url = 'https://api.cloudflare.com/client/v4/zones'
    response = get(url, headers=headers)
    if not response.ok:
        usage(code=5, message=response.json()['errors'][0]['message'])

    # look for domain zone
    res = response.json()['result']
    for dom in res:
        if dom['name'] == domain:
            return dom['id'] 
    usage(code=6, message=f'Domain "{domain}" not found for this account!\n')

def patchIP(newIP):
    zone = getZone()
    # get dns record id
    url = f'https://api.cloudflare.com/client/v4/zones/{zone}/dns_records'
    response = get(url, headers=headers)
    if not response.ok:
        usage(code=7, message=response.json()['errors'][0]['message'])
    zoneID = response.json()['result'][0]['id']

    # patch
    url += f'/{zoneID}'
    data = f'{{"type":"A","name":"{domain}","content":"{newIP}","ttl":1}}'
    response = patch(url, headers=headers, data=data)
    if not response.ok:
        usage(code=8, message=response.json()['errors'][0]['message'])

def log(record):
    with open(logFile, 'a') as fd:
        fd.write(record)

def main():
    # parse program arguments
    parse()
    try:
        localIP  = getLocalIP()
        publicIP = getPublicIP()

        if localIP != publicIP:
            # patch if change detected
            patchIP(localIP)
            log(record=f'{dt.now()}: {publicIP} -> {localIP}\n')
    except Exception as e:
        with open(errFile, 'a') as fd:
            fd.write(f'{e.output}')

if __name__ == '__main__':
    main()
