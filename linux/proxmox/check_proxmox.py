#!/usr/bin/env python3

import requests
import sys
import argparse

class checkproxmoxapi:
    
    def __init__(self, proxmoxip, proxmoxport, apitoken, oauthname, user):
        self.proxbaseurl = 'https://{0}:{1}/api2/json/'.format(proxmoxip, proxmoxport)
        self.apitoken = apitoken
        self.oauthname = oauthname
        self.user = user
        self.headers = {'Content-Type': 'application/json','Authorization': "PVEAPIToken={0}!{1}={2}".format(self.user, self.oauthname, self.apitoken)}
        self.connection = None
        requests.packages.urllib3.disable_warnings()

    def apiconnect(self):
        try:
            self.connection = requests.get((self.proxbaseurl), headers=self.headers, verify=False)
        except:
            print("Issue connecting to Proxmox at {0} with API token {2}".format(self.proxbaseurl, self.apitoken))

    def getvmdata(self,vmid,pveinstance):
        return requests.get(("{0}nodes/{1}/qemu/{2}/rrddata?timeframe=hour".format(self.proxbaseurl,pveinstance,vmid)), headers=self.headers, verify=False)
    
    def getlxcdata(self,lxcid,pveinstance):
        return requests.get(("{0}nodes/{1}/lxc/{2}/rrddata?timeframe=hour".format(self.proxbaseurl,pveinstance,lxcid)), headers=self.headers, verify=False)
    
    def getpvedata(self,pveinstance):
        return requests.get(("{0}nodes/{1}/rrddata?timeframe=hour".format(self.proxbaseurl,pveinstance)), headers=self.headers, verify=False)

def checkmetric(metric,curvalue,warn=None,crit=None):
    returndata = {}
    returndata['message'] = 'Unset'
    returndata['exitcode'] = 6

    if (warn is not None):
        if (metric > int(warn)):
            returndata['message'] = 'WARNING: {0} is {1}'.format(metric, curvalue)
            returndata['exitcode'] = 1

    if (crit is not None):
        if (metric > int(crit)):
            returndata['message'] = 'CRITICAL: {0} is {1}'.format(metric, curvalue)
            returndata['exitcode'] = 2
    
    if (returndata['exitcode'] == 6):
        returndata['message'] = 'OK: {0} is {1}'.format(metric,curvalue)
        returndata['exitcode'] = 0
    
    return returndata

def main():
    
    parser = argparse.ArgumentParser(prog='Check Proxmox via API')

    parser.add_argument('-H', '--host', required=True, type=str, help='The Proxmox host you wish to connect to.')
    parser.add_argument('-p', '--port', required=False, default='8006', type=str, help='The port Proxmox is listening on. Defaults to 8006 if not provided.')
    parser.add_argument('-o', '--oauthtoken', required=True, type=str, help='OAuth token for connecting to the API.')
    parser.add_argument('-O', '--oauthname', required=True, type=str, help='Name of OAuth token.')
    parser.add_argument('-u', '--user', required=True, type=str, help='User associated with the OAuth token. E.g. root@pam')

    subparsers = parser.add_subparsers(required=True, dest='toplvl', help='At which level would you like to collect metrics?')

    #parser_datacenter = subparsers.add_parser('datacenter')
    parser_pve = subparsers.add_parser('pve')
    parser_vm = subparsers.add_parser('vm')
    parser_lxc = subparsers.add_parser('lxc')

    parser_pve.add_argument('-p', '--pve', required=True, help='The name of the Proxmox server you wish to monitor.')
    parser_pve.add_argument('-m', '--metric', required=True, choices=['cpu', 'memory', 'netin', 'netout', 'swapused', 'iowait', 'loadavg', 'rootused'], help='The metric you would like to pull from the VM')
    parser_pve.add_argument('-w', '--warning', required=False, type=int, help='The warning value threshold. If the metric exceeds this value, a warning will be thrown.')
    parser_pve.add_argument('-c', '--critical', required=False, type=int, help='The critical value threshold. If the metric exceeds this value, a critical will be thrown.')

    parser_lxc.add_argument('-p', '--pve', required=True, help='The name of the Proxmox server where the LXC is running.')
    parser_lxc.add_argument('-i', '--lxcid', required=True, help='The Proxmox ID of the LXC you wish to monitor. E.g. 100')
    parser_lxc.add_argument('-m', '--metric', required=True, choices=['cpu', 'memory', 'diskread', 'diskwrite', 'netin', 'netout'], help='The metric you would like to pull from the LXC')
    parser_lxc.add_argument('-w', '--warning', required=False, type=int, help='The warning value threshold. If the metric exceeds this value, a warning will be thrown.')
    parser_lxc.add_argument('-c', '--critical', required=False, type=int, help='The critical value threshold. If the metric exceeds this value, a critical will be thrown.')

    parser_vm.add_argument('-p', '--pve', required=True, help='The name of the Proxmox server where the VM is running.')
    parser_vm.add_argument('-i', '--vmid', required=True, help='The Proxmox ID of the VM you wish to monitor. E.g. 100')
    parser_vm.add_argument('-m', '--metric', required=True, choices=['cpu', 'memory', 'diskread', 'diskwrite', 'netin', 'netout'], help='The metric you would like to pull from the VM')
    parser_vm.add_argument('-w', '--warning', required=False, type=int, help='The warning value threshold. If the metric exceeds this value, a warning will be thrown.')
    parser_vm.add_argument('-c', '--critical', required=False, type=int, help='The critical value threshold. If the metric exceeds this value, a critical will be thrown.')

    parsedargs = parser.parse_args(sys.argv[1:])

    myprox = checkproxmoxapi(parsedargs.host, parsedargs.port, parsedargs.oauthtoken, parsedargs.oauthname, parsedargs.user)

    myresults = float()
    metricdata = {}

    # Determine from which level we are grabbing metrics.
    if (parsedargs.toplvl == 'datacenter'):
        # For datacenter level metrics
        pass
    
    elif (parsedargs.toplvl == 'pve'):
        if (parsedargs.metric == 'cpu'):
            myresults = round(float(myprox.getpvedata(parsedargs.pve).json()['data'][69]['cpu']),2)
        elif (parsedargs.metric == 'memory'):
            myresults = round(float(myprox.getpvedata(parsedargs.pve).json()['data'][69]['memused']),2)
        elif (parsedargs.metric == 'iowait'):
            myresults = round(float(myprox.getpvedata(parsedargs.pve).json()['data'][69]['iowait']),2)
        elif (parsedargs.metric == 'swapused'):
            myresults = round(float(myprox.getpvedata(parsedargs.pve).json()['data'][69]['swapused']),2)
        elif (parsedargs.metric == 'rootused'):
            myresults = round(float(myprox.getpvedata(parsedargs.pve).json()['data'][69]['rootused']),2)
        elif (parsedargs.metric == 'netin'):
            myresults = round(float(myprox.getpvedata(parsedargs.pve).json()['data'][69]['netin']),2)
        elif (parsedargs.metric == 'netout'):
            myresults = round(float(myprox.getpvedata(parsedargs.pve).json()['data'][69]['netout']),2)

        metricdata = checkmetric(parsedargs.metric,myresults)

    elif (parsedargs.toplvl == 'lxc'):
        if (parsedargs.metric == 'cpu'):
            myresults = round(float(myprox.getlxcdata(parsedargs.lxcid,parsedargs.pve).json()['data'][69]['cpu']),2)
        elif (parsedargs.metric == 'memory'):
            myresults = round(float(myprox.getlxcdata(parsedargs.lxcid,parsedargs.pve).json()['data'][69]['mem']),2)
        elif (parsedargs.metric == 'diskread'):
            myresults = round(float(myprox.getlxcdata(parsedargs.lxcid,parsedargs.pve).json()['data'][69]['diskread']),2)
        elif (parsedargs.metric == 'diskwrite'):
            myresults = round(float(myprox.getlxcdata(parsedargs.lxcid,parsedargs.pve).json()['data'][69]['diskwrite']),2)
        elif (parsedargs.metric == 'netin'):
            myresults = round(float(myprox.getlxcdata(parsedargs.lxcid,parsedargs.pve).json()['data'][69]['netin']),2)
        elif (parsedargs.metric == 'netout'):
            myresults = round(float(myprox.getlxcdata(parsedargs.lxcid,parsedargs.pve).json()['data'][69]['netout']),2)

        metricdata = checkmetric(parsedargs.metric,myresults)

    elif (parsedargs.toplvl == 'vm'):
        if (parsedargs.metric == 'cpu'):
            myresults = round(float(myprox.getvmdata(parsedargs.vmid,parsedargs.pve).json()['data'][69]['cpu']),2)
        elif (parsedargs.metric == 'memory'):
            myresults = round(float(myprox.getvmdata(parsedargs.vmid,parsedargs.pve).json()['data'][69]['mem']),2)
        elif (parsedargs.metric == 'diskread'):
            myresults = round(float(myprox.getvmdata(parsedargs.vmid,parsedargs.pve).json()['data'][69]['diskread']),2)
        elif (parsedargs.metric == 'diskwrite'):
            myresults = round(float(myprox.getvmdata(parsedargs.vmid,parsedargs.pve).json()['data'][69]['diskwrite']),2)
        elif (parsedargs.metric == 'netin'):
            myresults = round(float(myprox.getvmdata(parsedargs.vmid,parsedargs.pve).json()['data'][69]['netin']),2)
        elif (parsedargs.metric == 'netout'):
            myresults = round(float(myprox.getvmdata(parsedargs.vmid,parsedargs.pve).json()['data'][69]['netout']),2)

        metricdata = checkmetric(parsedargs.metric,myresults)

    print(metricdata['message'])
    exit(metricdata['exitcode'])

if __name__ == '__main__':
    main()