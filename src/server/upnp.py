import subprocess
import random

'''
I was having issues with the upnpy module regarding timeout of new connections. 
This is a hacky but functional implementation of UPnP port forwarding using the
upnpc command line tool.
'''


def upnp_discoverUPnPDevices():
    result = subprocess.run(['upnpc', '-l'], capture_output=True, text=True)
    output = result.stdout

    if result.returncode != 0:
        print("Result of command: ", result)
        if "command not found" in result.stderr:
            raise RuntimeError("upnpc command not found")
        else:
            print(f"Command failed with error: {result.stderr}")
            return False

    if "Found valid IGD" in output:
        return True
    else:
        return False
    

def upnp_newPortForwardingRule(ownIpAddress, middlewarePort):
    # get current port redirections
    result = subprocess.run(['upnpc', '-l'], capture_output=True, text=True)
    output = result.stdout

    if result.returncode != 0:
        print("Result of command: ", result)
        if "command not found" in result.stderr:
            raise RuntimeError("upnpc command not found")
        else:
            print(f"Command failed with error: {result.stderr}")
            return False, 0


    # Parse the output to find currently used ports
    used_ports = set()
    for line in output.splitlines():
        parts = line.split()
        if len(parts) > 4 and parts[0].isdigit():
            protocol = parts[1]
            ex_port = parts[2].split('->')[0]
            used_ports.add((protocol, ex_port))

    print("Found out that used ports are: ", used_ports)

    # Find random port between 40000 and 60000 that is not already used
    while True:
        externalPort = str(random.randint(40000, 60000))
        if ('TCP', externalPort) not in used_ports:
            break

    # upnpc -e "MyApp" -a 192.168.1.160 34567 34567 TCP
    result = subprocess.run(['upnpc', '-e', 'MyApp', '-a', str(ownIpAddress), str(externalPort), str(middlewarePort), 'TCP'], capture_output=True, text=True)

    if result.returncode != 0:
        print("Result of command: ", result)
        if "command not found" in result.stderr:
            raise RuntimeError("upnpc command not found")
        else:
            print(f"Command failed with error: {result.stderr}")
            return False, 0


    if "is redirected to internal" in result.stdout:
        return True, externalPort
    else:
        return False, 0