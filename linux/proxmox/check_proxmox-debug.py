#!/usr/bin/env python3

import requests
import sys
import argparse

class checkproxmoxapi:
    
    def __init__(self, proxmoxip, proxmoxport, tokenID, secret):
        self.proxmoxip = proxmoxip
        self.proxmoxport = proxmoxport
        self.proxbaseurl = 'https://{0}:{1}/api2/json/'.format(proxmoxip, proxmoxport)
        self.tokenID = tokenID
        self.secret = secret
        self.connection = None
        requests.packages.urllib3.disable_warnings()

        self.headers = {
            'Content-Type': 'x-www-form-urlencoded',
            'Authorization': f"PVEAPIToken={self.tokenID}={self.secret}"
        }

    def getvmdata(self, vmid, pveinstance):
        return requests.get(
            f"{self.proxbaseurl}nodes/{pveinstance}/qemu/{vmid}/rrddata?timeframe=hour",
            headers=self.headers,
            verify=False
        )

    def getlxcdata(self, lxcid, pveinstance):
        return requests.get(
            f"{self.proxbaseurl}nodes/{pveinstance}/lxc/{lxcid}/rrddata?timeframe=hour",
            headers=self.headers,
            verify=False
        )
    
    def getpvedata(self, pveinstance):
        return requests.get(
            f"{self.proxbaseurl}nodes/{pveinstance}/",
            headers=self.headers,
            verify=False
        )
    
    def getpoolslist(self):
        return requests.get(
            f"{self.proxbaseurl}pools/",
            headers=self.headers,
            verify=False
        )
    
    def getpoolsdata(self, poolinstance):
        return requests.get(
            f"{self.proxbaseurl}pools/{poolinstance}/",
            headers=self.headers,
            verify=False
        )
  

## TODO:
# Implement the logic to check metrics and handle the response from the API.
# Implement the ability to check all pools, then show the cpu usage of each pool.
#   Also implement the ability to check a specific pool and return the cpu usage of that pool.
#   Also so all of the vms in that pool, and return the cpu usage of each vm in that pool.
def main():
    
    parser = argparse.ArgumentParser(prog='Check Proxmox via API')
    parser.add_argument('-H', '--host', required=True, default='192.168.0.100', type=str, help='The Proxmox host you wish to connect to.')
    parser.add_argument('-p', '--port', required=False, default='8006', type=str, help='The port Proxmox is listening on. Defaults to 8006 if not provided.')
    parser.add_argument('-t', '--tokenID', required=True, default='root@pam!main', type=str, help='Full tokenID for example root@pam!main.')
    parser.add_argument('-s', '--secret', required=True, default='a482c573-3a2b-45b5-ae96-dce53be5d9fe', type=str, help='Secret password for the API key.')
    parser.add_argument('--pool', required=False, default='Monitoring', type=str, help='What is the pool to monitor.')

    parsedargs = parser.parse_args(sys.argv[1:])
    print("Parsed arguments:", parsedargs)  # Debug print

    myprox = checkproxmoxapi(parsedargs.host, parsedargs.port, parsedargs.oauthtoken, parsedargs.oauthname, parsedargs.user)

    myresults = float()
    metricdata = {}

    # Determine from which level we are grabbing metrics.
    if (parsedargs.toplvl == 'datacenter'):
        # For datacenter level metrics
        pass
    
    elif (parsedargs.toplvl == 'pve'):
        try:
            api_response = myprox.getpvedata(parsedargs.pve)
            json_data = api_response.json()
            print("API response:", json_data)  # Debug print
            print("Data length:", len(json_data.get('data', [])))
            myresults = round(float(json_data['data'][69][parsedargs.metric]),2)
        except (KeyError, IndexError) as e:
            print("Plugin Error: {0}. Setting to UNKNOWN".format(e))
            exit(3)

        metricdata = checkmetric(parsedargs.metric,myresults)

    elif (parsedargs.toplvl == 'lxc'):
        try:
            myresults = round(float(myprox.getlxcdata(parsedargs.lxcid,parsedargs.pve).json()['data'][69][parsedargs.metric]),2)
        except (KeyError, IndexError) as e:
            print("Plugin Error: {0}. Setting to UNKNOWN".format(e))
            exit(3)            

        metricdata = checkmetric(parsedargs.metric,myresults)

    elif (parsedargs.toplvl == 'vm'):
        try:
            myresults = round(float(myprox.getvmdata(parsedargs.vmid,parsedargs.pve).json()['data'][69][parsedargs.metric]),2)
        except (KeyError, IndexError) as e:
            print("Plugin Error: {0}. Setting to UNKNOWN".format(e))
            exit(3)

        metricdata = checkmetric(parsedargs.metric,myresults,parsedargs.warning,parsedargs.critical)

    print('{0} | {1}'.format(metricdata['message'], metricdata['perfdata']))
    exit(metricdata['exitcode'])

if __name__ == '__main__':
  main()
