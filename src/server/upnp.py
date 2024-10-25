import subprocess
import random

'''
I was having issues with the upnpy module regarding timeout of new connections. 
This is a hacky but functional implementation of UPnP port forwarding using the
upnpc command line tool.
'''


def upnp_getAllPortForwardingRules():
    result = subprocess.run(['upnpc', '-l'], capture_output=True, text=True)
    output = result.stdout

    if result.returncode != 0:
        if "command not found" in result.stderr:
            raise RuntimeError("upnpc command not found")
        else:
            return False

    # Parse the output to find currently used ports
    used_ports = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) > 4 and parts[0].isdigit():
            protocol = parts[1]
            ex_port = parts[2].split('->')[0]
            forwarding_name = parts[3]
            used_ports.add((protocol, ex_port, forwarding_name))
    
    return used_ports


def upnp_getTorPortForwardingRules():
    currentRules = upnp_getAllPortForwardingRules()
    filteredRules = set()

    for rule in currentRules:
        if rule[3] == "p2p-messenger":
            filteredRules.add(rule)
        
    return filteredRules



def upnp_discoverUPnPDevices():
    currentRules = upnp_getAllPortForwardingRules()

    return currentRules is not False
    

def upnp_removePortForwardingRule(externalPort):
    print(f"->>> Removing UPnP port forwarding rule for port {externalPort}")

    result = subprocess.run(['upnpc', '-d', str(externalPort), 'TCP'], capture_output=True, text=True)

    if result.returncode != 0:
        if "command not found" in result.stderr:
            raise RuntimeError("upnpc command not found")
        else:
            print(f"Command failed with error: {result.stderr}")
            return False

    return True


def upnp_cleanupPortForwardingRules():
    print("->>> Cleaning up UPnP port forwarding rules")

    currentRules = upnp_getAllPortForwardingRules()

    print(currentRules)

    if currentRules is False:
        return False
    
    for rule in currentRules:
        if "p2p-messenger" in rule[2]:
            print("Routing rule found, removing it")
            upnp_removePortForwardingRule(rule[1])
    
    return True
    

def upnp_newPortForwardingRule(ownIpAddress, internalPort):
    # get current port redirections
    if upnp_discoverUPnPDevices() is False:
        return False, 0

    currentRules = upnp_getAllPortForwardingRules()
    used_ports = set()
    for rule in currentRules:
        used_ports.add(rule[1])

    # Find random port between 60001 and 60000 that is not already used
    while True:
        externalPort = str(random.randint(60001, 63000))
        if ('TCP', externalPort) not in used_ports:
            break

    result = subprocess.run(['upnpc', '-e', 'p2p-messenger', '-a', str(ownIpAddress), str(internalPort), str(externalPort), 'TCP'], capture_output=True, text=True)

    currentRules = upnp_getAllPortForwardingRules()
    ruleAdded = False
    for rule in currentRules:
        if "p2p-messenger" in rule[2]:
            ruleAdded = True
            break
    
    if ruleAdded is False:
        print("Failed to add UPnP port forwarding rule")
        return False, 0
    
    print("DONE adding UPnP port forwarding rule on port", externalPort)
    
    return True, externalPort