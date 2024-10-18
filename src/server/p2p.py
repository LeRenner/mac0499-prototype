import flask
import requests
import json
import base64
import datetime
import socket
from time import sleep
import threading
import multiprocessing

from .serverCrypto import *
from .jsonOperator import *
from .friends import *
from .upnp import *

global currentFocusedFriend
global friendConnectionThread
global friendUpdateThread
global localSocksPort
global statusIndicatorBadge
global friendConnectionStatus
global friendConnectionDetails


def p2p_initializeVariables(rcvSocksPort):
    global friendConnectionThread
    global friendUpdateThread
    global localSocksPort
    global currentFocusedFriend
    global statusIndicatorBadge
    global friendConnectionStatus
    global friendConnectionDetails

    localSocksPort = rcvSocksPort
    currentFocusedFriend = None
    statusIndicatorBadge = None
    friendConnectionThread = None
    friendConnectionStatus = 0
    friendConnectionDetails = {
        "middlewarePort": None,
        "friendPublicAddress": None,
        "friendLocalAddress": None
    }
    friendUpdateThread = threading.Thread(target=p2p_friendUpdateThread)
    friendUpdateThread.start()


#####################################################
######## P2P THREADS ################################
#####################################################

def p2p_friendConnectionThread():
    while True:
        waitTime = p2p_tryConnecting()
        if waitTime == -1:
            break
        sleep(waitTime)


def p2p_tryConnecting():
    global currentFocusedFriend
    global statusIndicatorBadge
    global friendConnectionStatus

    print("Current focused friend: " + str(currentFocusedFriend))
    print("Status indicator badge: " + str(statusIndicatorBadge))

    if currentFocusedFriend == "00000000000000000000000000000000000000000000000000000000.onion":
        statusIndicatorBadge = "None."
        return -1

    print("Trying to connect to friend.")
    print("statusIndicatorBadge: ", statusIndicatorBadge)

    statusIndicatorBadge = "Checking if friend is mutual..."

    focusedFriendIsMutual = friends_checkIsMutualFriend(currentFocusedFriend)

    print("Focused friend is mutual: ", focusedFriendIsMutual)
    print("Current focused friend: ", currentFocusedFriend)

    if focusedFriendIsMutual == False:
        print("Friend is not mutual.")
        statusIndicatorBadge = "Friend is not mutual."
        return 20

    statusIndicatorBadge = "Waiting for friend to focus on you..."

    while True:
        print("Status indicator badge: ", statusIndicatorBadge)
        sleep(1)

    print("Waiting for friend to focus on you...", end="")
    print("Current focused friend: ", currentFocusedFriend)

    while friends_checkIsFocusedFriend(currentFocusedFriend) == False:
        print(".", end="")
        sleep(5)

    statusIndicatorBadge = "Getting friend's IP addresses..."

    print("Getting friend's IP addresses...")
    print("Current focused friend: ", currentFocusedFriend)

    friendIPs = friends_getFriendIpAddress(currentFocusedFriend)

    print("Friend IPs: ", friendIPs)
    print("Current focused friend: ", currentFocusedFriend)

    friendConnectionDetails["middlewarePort"] = friendIPs["middlewarePort"]
    friendConnectionDetails["friendPublicAddress"] = friendIPs["public"]
    friendConnectionDetails["friendLocalAddress"] = friendIPs["local"]



    # if users are on the same machine, friendConnectionStatus = 1
    if friendIPs["public"] == p2p_getPublicIP() and friendIPs["local"] == p2p_getLocalIP():
        return p2p_localhostConnection()


    # if users are on the same local network, friendConnectionStatus = 2
    if friendIPs["public"] == p2p_getPublicIP():
        return p2p_localNetworkConnection()
    

    # if users are on different networks, friendConnectionStatus = 3
    if friendIPs["public"] != p2p_getPublicIP():
        return p2p_UPnPConnection()

    print("REACHED END OF TRYCONNECTING. EXITING.")
    return -1


def p2p_friendUpdateThread():
    global currentFocusedFriend
    global friendConnectionThread

    pastFocusedFriend = None

    while True:
        print("=============================================")
        print("Started! currentFocusedFriend: ", currentFocusedFriend)
        print("pastFocusedFriend: ", pastFocusedFriend)

        while currentFocusedFriend == pastFocusedFriend:
            sleep(1)

        print("Focused friend changed. Updating connection thread.")
        
        pastFocusedFriend = currentFocusedFriend

        if currentFocusedFriend is None or "00000000000000000000000000000000000000000" in currentFocusedFriend:
            try:
                print("Killing thread.")
                friendConnectionThread.terminate()
            except AttributeError:
                print("No thread to terminate.")

            except AttributeError:
                print("No thread to join.")
        else:
            print("Starting new thread.")
            # start friend connection thread
            friendConnectionThread = multiprocessing.Process(target=p2p_friendConnectionThread)
            friendConnectionThread.start()
        
        print("Reached the end???????????")

        sleep(1)


#####################################################
######## P2P CONNECTIONS ############################
#####################################################

def p2p_localhostConnection():
    global friendConnectionStatus
    global statusIndicatorBadge
    global currentFocusedFriend

    friendConnectionStatus = 1
    statusIndicatorBadge = "Connected on localhost!"

    while True:
        try:
            requestMethod = {
                "hostname": f"http://localhost:{friendConnectionDetails['middlewarePort']}/pubEndpoint_receiveGenericFriendRequest",
                "proxy": None
            }
            isFocused = friends_checkIsFocusedFriend(currentFocusedFriend, requestMethod)

            if isFocused == False:
                statusIndicatorBadge = "Friend closed chat with you. Defaulting to tor."
                return 1
        except requests.RequestException:
            statusIndicatorBadge = "Friend connection lost."
            return 1
                
        sleep(1)


def p2p_localNetworkConnection():
    friendConnectionStatus = 2
    statusIndicatorBadge = "OMG local network but it still doesnt work!"
    return -1


def p2p_UPnPConnection():
    global friendConnectionStatus
    global statusIndicatorBadge
    global friendConnectionDetails

    friendConnectionStatus = 3
    statusIndicatorBadge = "On different networks! Will try to UPNP port forward."

    # try to UPNP port forward
    hasUPnP = upnp_discoverUPnPDevices()

    if hasUPnP == False:
        statusIndicatorBadge = "No UPnP devices found."
        friends_updateUPnPStatus(False, 0)

        # check if friend has UPnP
        while friends_getUPnPStatus(currentFocusedFriend) == None:
            print("Waiting for friend to check UPnP status.")
            sleep(5)
    else:
        success, externalport = upnp_newPortForwardingRule(p2p_getPublicIP(), friendConnectionDetails["middlewarePort"])

        if not success:
            statusIndicatorBadge = "Failed to UPnP port forward."
            friends_updateUPnPStatus(False, 0)
            return 10

        friends_updateUPnPStatus(True, externalport)

        statusIndicatorBadge = "UPnP port forwarding successful! Checking in with friend..."

        while True:
            result = friends_getUPnPStatus(currentFocusedFriend)
            print("On UPnP connection, result is: ", result)
            console.log(result)


#####################################################
######## P2P FUNCTIONS ##############################
#####################################################

def p2p_processFirstContact(address):
    global localSocksPort

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    for i in range(3):
        try:
            response = requests.get(f"http://{address}/pubEndpoint_getPublicKeyBase64", proxies=proxies, timeout=15)
            if response.status_code == 200:
                response_data = response.json()
                public_key = response_data.get("public_key")
                if public_key:
                    operator_storePeerPublicKey(address, public_key)
                    operator_successFirstContact(address)
                    return
        except requests.RequestException as e:
            print(f"Attempt {i+1} failed.")
        sleep(1)

    operator_removeFirstContact(address)
    print("Failed to retrieve public key after 3 attempts.")


def p2p_getPublicIP():
    try:
        response = requests.get("http://httpbin.org/ip")
        return response.json()["origin"]
    except requests.exceptions.RequestException:
        return None


def p2p_receiveFriendIsFocusedRequest(request_object_json: str) -> bool:
    global currentFocusedFriend
    result = friends_receiveGenericFriendRequest(request_object_json, "isFocused")

    if result is not True:
        return result

    origin = json.loads(json.loads(request_object_json)["request"])["origin"]

    if currentFocusedFriend == origin:
        return {"message": "Success", "isFocused": True}
    else:
        return {"message": "Success", "isFocused": False}


def p2p_getLocalIP():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip


def p2p_checkIfIsFocusedFriend(address):
    global currentFocusedFriend

    if currentFocusedFriend == address:
        return {"status": "Focused"}
    else:
        return {"status": "Not focused"}


def p2p_changeFocusedFriend(address):
    global currentFocusedFriend

    if address == "null":
        currentFocusedFriend = None
    else:
        currentFocusedFriend = address

    return {"status": "Success"}


def p2p_getstatusIndicatorBadge():
    global statusIndicatorBadge

    print("Status indicator badge: ", statusIndicatorBadge)

    if statusIndicatorBadge is None:
        return {"status": "No friend connection status available."}

    return {"status": statusIndicatorBadge}


# 0 = not connected
# 1 = connected on localhost
# 2 = connected on local network
# 3 = connected on p2p
def p2p_getFriendConnectionStatus():
    global friendConnectionStatus
    global friendConnectionDetails

    if friendConnectionStatus == 0:
        return {"status": "0"}
    
    if friendConnectionStatus == 1:
        return {"status": "1", "middlewarePort": friendConnectionDetails["middlewarePort"]}

    return friendConnectionStatus