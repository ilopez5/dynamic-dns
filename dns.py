#!/bin/python3
from datetime import datetime as dt
from requests import get, patch
from socket   import gethostbyname
from getopt   import getopt, GetoptError
from os       import getenv, path
import sys

# globals
domain  = 'example.com'
logFile = 'dns.out.log'
errFile = 'dns.err.log'

headers = {
    'X-Auth-Email': getenv('CF_EMAIL'),
    'X-Auth-Key'  : getenv('CF_TOKEN'),
    'Content-Type': 'application/json',
}

def parse():
    global domain, logFile, errFile
    # collect program arguments
    try:
        opts, args = getopt(sys.argv[1:], "hd:o:e:", ["help", "output=", "error="])
    except GetoptError as error:
        usage(code=1, message=error)

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
            usage(2, f'Unhandled option: {opt}. See -h for usage.')
    return

def usage(code=0, message=None):
    file_name = path.basename(__file__)
    print(message if code else '')
    print(f"Usage: python3 {file_name} [-d example.com] [OPTIONS]\n"
            "\t-d\tTop-Level Domain (DNS managed by Cloudflare)\n"
            "\t-o\tOutput log file\n"
            "\t-e\tError file.")
    sys.exit(code)

def getMyIP():
    return get('https://api.ipify.org').text

def getPublicIP():
    return gethostbyname(sys.argv[1])

def getZone():
    # ping to get zone
    url = 'https://api.cloudflare.com/client/v4/zones'
    response = get(url, headers=headers).json()['result']
    # look for domain zone
    for domain in response:
        if domain['name'] == sys.argv[1]:
            return domain['id'] 
    raise Exception

def patchIP(new_ip):
    zone = getZone()
    # get dns record id
    url = f'https://api.cloudflare.com/client/v4/zones/{zone}/dns_records'
    zone_id = get(url, headers=headers).json()['result'][0]['id']

    # patch
    url += f'/{zone_id}'
    data = f'{{"type":"A","name":"{sys.argv[1]}","content":"{new_ip}","ttl":1}}'
    response = patch(url, headers=headers, data=data)
    return

def log(old_ip, new_ip):
    with open(sys.argv[2], "a") as fd:
        fd.write(f"{dt.now()}: {old_ip} -> {new_ip}\n")
    return

def main():
    parse()
    sys.exit(0)
    try:
        current_ip = getMyIP()
        public_ip  = getPublicIP()

        if current_ip != public_ip:
            patchIP(current_ip)
            log(public_ip, current_ip)
    except Exception as e:
        with open("error.txt", "a") as fd:
            fd.write(f"{e.output}")

if __name__ == '__main__':
    main()
