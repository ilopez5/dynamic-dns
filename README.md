# DynamicDNS

**Ismael J Lopez**

## Overview
Static IP addresses often cost money with Internet Service Providers.
If you own a domain and manage the DNS with Cloudflare, you can
leverage its API to *dynamically* update the DNS records with the new
IP address an ISP assigns to you when it changes. This is typically
called DynamicDNS.

## Build
Only standard libraries are used. Use with Python 3.

## Usage
Run like so:
```bash
$ python3 dns.py -d example.com
```
For help instructions, run with the `-h` flag.

## Suggested Use
Add a `crontab` entry to run this command periodically on a device
that is always on, such as a Raspberry Pi. If you set it to run every
30 minutes, you ensure a maximum downtime of 30 minutes if the IP
were to change just after the most recent run.
