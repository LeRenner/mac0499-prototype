import flask
import requests
import json
import base64
import datetime
import socket
# import upnpy
from time import sleep
import threading

from .serverCrypto import *
from .jsonOperator import *
from .friends import *

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

    if currentFocusedFriend == "00000000000000000000000000000000000000000000000000000000.onion":
        statusIndicatorBadge = "None."
        return -1

    statusIndicatorBadge = "Checking if friend is mutual..."

    focusedFriendIsMutual = friends_checkIsMutualFriend(currentFocusedFriend)

    if focusedFriendIsMutual == False:
        statusIndicatorBadge = "Friend is not mutual."
        return 20

    statusIndicatorBadge = "Waiting for friend to focus on you..."

    while friends_checkIsFocusedFriend(currentFocusedFriend) == False:
        sleep(5)

    statusIndicatorBadge = "Getting friend's IP addresses..."

    friendIPs = friends_getFriendIpAddress(currentFocusedFriend)

    # {"local": localIp, "public": publicIp, "middlewarePort": localMiddlewarePort}   
    # friendConnectionDetails = {
    #     "middlewarePort": None,
    #     "friendPublicAddress": None,
    #     "friendLocalAddress": None
    # }
    friendConnectionDetails["middlewarePort"] = friendIPs["middlewarePort"]
    friendConnectionDetails["friendPublicAddress"] = friendIPs["public"]
    friendConnectionDetails["friendLocalAddress"] = friendIPs["local"]

    # if users are on the same machine, friendConnectionStatus = 1
    if friendIPs["public"] == p2p_getPublicIP() and friendIPs["local"] == p2p_getLocalIP():
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
    

    if friendIPs["public"] == p2p_getPublicIP():
        friendConnectionStatus = 2
        statusIndicatorBadge = "Connected on local network!"
        return 1
    

    # if friendIPs["public"] != p2p_getPublicIP():
    #     friendConnectionStatus = 3
    #     statusIndicatorBadge = "On different networks! Will try to UPNP port forward."

    #     # try to UPNP port forward
    #     try:
    #         upnp = upnpy.UPnP()
    #         upnp.discover()
    #         upnp.select_igd()
    #         upnp.get_status_info()
    #         upnp.get_port_mappings()
    #         upnp.add_port_mapping(friendConnectionDetails["middlewarePort"], "TCP", "P2P Middleware Port", "
        

    # while True:
    #     print("DIED DIED DIED")
    #     sleep(1)


def p2p_friendUpdateThread():
    global currentFocusedFriend
    global friendConnectionThread

    pastFocusedFriend = None

    while True:
        while currentFocusedFriend == pastFocusedFriend:
            sleep(1)
        
        pastFocusedFriend = currentFocusedFriend

        if currentFocusedFriend is None or currentFocusedFriend == "00000000000000000000000000000000000000000000000000000000.onion":
            if friendConnectionThread is not None:
                # kill friend connection thread
                friendConnectionThread.join()
                break
        else:
            # start friend connection thread
            friendConnectionThread = threading.Thread(target=p2p_friendConnectionThread)
            friendConnectionThread.start()
        
        sleep(1)


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