import flask
import requests
import json
import base64
import datetime
import socket
import random
from time import sleep
import threading

from .serverCrypto import *
from .jsonOperator import *
from .friends import *
from .upnp import *

global p2p_status


def p2p_initializeVariables(rcvSocksPort, rcvLocalMiddlewarePort):
    global p2p_status

    p2p_status = {
        #############################################################
        ######## GENERAL VARIABLES ##################################
        #############################################################
        "general_shouldKillConnectionThread": False,
        "general_socksPort": rcvSocksPort,
        "general_localMiddlewarePort": rcvLocalMiddlewarePort,
        "general_currentFocusedFriend": None,
        "general_clientConnectionMessage": None,

        # 0 = not connected
        # 1 = connected on localhost
        # 2 = connected on local network
        # 3 = connected on p2p
        "friendConnectionStatus": 0,

        # for connections on localhost; friend's middleware port        
        "localhost_friendMiddlewarePort": None,

        # friend's addresses
        "friendPublicAddress": None,
        "friendLocalAddress": None,
        "friendUpnpInformation": None,

        # for local network connections
        "localConnectionPort": None,
        "externalConnectionPort": None,

        # socket direct network connections
        "directConnectionSocket": None,

        # threads that manage peer-to-peer connections
        "friendUpdateThread": threading.Thread(target=p2p_friendUpdateThread),
        "friendConnectionThread": None
    }
    p2p_status["friendUpdateThread"].start()


def p2p_resetConnectionVariables():
    global p2p_status

    p2p_status["general_shouldKillConnectionThread"] = False
    p2p_status["general_clientConnectionMessage"] = None
    p2p_status["friendConnectionStatus"] = 0
    p2p_status["localhost_friendMiddlewarePort"] = None
    p2p_status["friendPublicAddress"] = None
    p2p_status["friendLocalAddress"] = None
    p2p_status["localConnectionPort"] = None
    p2p_status["directConnectionSocket"] = None
    p2p_status["friendConnectionThread"] = None


#####################################################
######## P2P THREADS ################################
#####################################################

def p2p_friendConnectionThread():
    while True:
        waitTime = p2p_tryConnecting()
        if waitTime == -1:
            break
        sleep(waitTime)


def p2p_connectionThreadDying():
    global p2p_status

    p2p_status["general_shouldKillConnectionThread"] = False
    return -1


def p2p_tryConnecting():
    global p2p_status

    friends_resetConnectionVariables()
    p2p_resetConnectionVariables()


    if p2p_status["general_currentFocusedFriend"] == "00000000000000000000000000000000000000000000000000000000.onion":
        p2p_status["general_clientConnectionMessage"] = "None."
        return -1

    # check if connection thread should die
    if p2p_status["general_shouldKillConnectionThread"]: return p2p_connectionThreadDying()

    p2p_status["general_clientConnectionMessage"] = "Checking if friend is mutual..."

    focusedFriendIsMutual = friends_checkIsMutualFriend(p2p_status["general_currentFocusedFriend"])

    # check if connection thread should die
    if p2p_status["general_shouldKillConnectionThread"]: return p2p_connectionThreadDying()

    if focusedFriendIsMutual == False:
        print("Friend is not mutual.")
        p2p_status["general_clientConnectionMessage"] = "Friend is not mutual."
        return 20

    p2p_status["general_clientConnectionMessage"] = "Waiting for friend to focus on you..."

    while friends_checkIsFocusedFriend(p2p_status["general_currentFocusedFriend"]) == False:
        # check if connection thread should die
        if p2p_status["general_shouldKillConnectionThread"]: return p2p_connectionThreadDying()

        print(".", end="")
        sleep(5)
    

    # check if connection thread should die
    if p2p_status["general_shouldKillConnectionThread"]: return p2p_connectionThreadDying()


    p2p_status["general_clientConnectionMessage"] = "Getting friend's IP addresses..."

    friendIPs = friends_getFriendIpAddress(p2p_status["general_currentFocusedFriend"])

    # check if connection thread should die
    if p2p_status["general_shouldKillConnectionThread"]: return p2p_connectionThreadDying()

    p2p_status["localhost_friendMiddlewarePort"] = friendIPs["middlewarePort"]
    p2p_status["friendPublicAddress"] = friendIPs["public"]
    p2p_status["friendLocalAddress"] = friendIPs["local"]

    # if users are on the same machine, friendConnectionStatus = 1
    if friendIPs["public"] == p2p_getPublicIP() and friendIPs["local"] == friends_getLocalIP():
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
    global p2p_status

    pastFocusedFriend = None

    while True:
        print("=============================================")
        print("Started! p2p_status[focusedFriend]: ", p2p_status["general_currentFocusedFriend"])

        while p2p_status["general_currentFocusedFriend"] == pastFocusedFriend:
            sleep(1)
        
        pastFocusedFriend = p2p_status["general_currentFocusedFriend"]

        if p2p_status["general_currentFocusedFriend"] is None or "00000000000000000000000000000000000000000" in p2p_status["general_currentFocusedFriend"]:
            try:
                print("Killing thread.")
                p2p_status["friendConnectionThread"].terminate()
            except AttributeError:
                print("No thread to terminate.")

            except AttributeError:
                print("No thread to join.")
        else:
            print("Starting new thread.")
            # start friend connection thread
            p2p_status["friendConnectionThread"] = threading.Thread(target=p2p_friendConnectionThread)
            p2p_status["friendConnectionThread"].start()
        
        print("Reached the end???????????")

        sleep(1)


#####################################################
######## P2P CONNECTIONS ############################
#####################################################

def p2p_localhostConnection():
    global p2p_status

    friendConnectionStatus = 1
    p2p_status["general_clientConnectionMessage"] = "Connected on localhost!"

    while True:
        # check if connection thread should die
        if p2p_status["general_shouldKillConnectionThread"]: return p2p_connectionThreadDying()

        try:
            requestMethod = {
                "hostname": f"http://localhost:{friendConnectionDetails['general_localMiddlewarePort']}/pubEndpoint_receiveGenericFriendRequest",
                "proxy": None
            }
            isFocused = friends_checkIsFocusedFriend(p2p_status["general_currentFocusedFriend"], requestMethod)

            if isFocused == False:
                p2p_status["general_clientConnectionMessage"] = "Friend closed chat with you. Defaulting to tor."
                return 1
        except requests.RequestException:
            p2p_status["general_clientConnectionMessage"] = "Friend connection lost."
            return 1
                
        sleep(1)


def p2p_localNetworkConnection():
    global p2p_status

    friendConnectionStatus = 2
    p2p_status["general_clientConnectionMessage"] = "Connecting on local network..."

    # Determine which peer will host the connection
    if crypto_getOwnAddress() > p2p_status["general_currentFocusedFriend"]:
        return p2p_localNetworkHostServer()
    else:
        return p2p_localNetworkConnectToServer()

    return


def p2p_UPnPConnection():
    global p2p_status

    friendConnectionStatus = 3
    p2p_status["general_clientConnectionMessage"] = "On different networks! Will try to UPNP port forward."

    upnp_cleanupPortForwardingRules()

    # try to UPNP port forward
    hasUPnP = upnp_discoverUPnPDevices()

    if hasUPnP == False:
        p2p_status["general_clientConnectionMessage"] = "No UPnP devices found."
        friends_updateUPnPStatus(False, False, 0)

        # check if friend has UPnP
        while True:
            if "0000000000000000000000000000000000" in p2p_status["general_currentFocusedFriend"]: return 0

            friendUpnpStatus = friends_getUPnPStatus(p2p_status["general_currentFocusedFriend"])

            print("I dont have UPNP. Friend's UPNP status is: ", friendUpnpStatus)

            if friendUpnpStatus["hasSupport"] == False:
                p2p_status["general_clientConnectionMessage"] = "Friend does not have UPnP support. Defaulting to tor."
                return -1
            
            if friendUpnpStatus["readyForConnection"] == False:
                p2p_status["general_clientConnectionMessage"] = "Friend is not ready for connection. Waiting..."
                sleep(3)
                continue
            
            if friendUpnpStatus["readyForConnection"] == True and friendUpnpStatus["upnpPort"] != 0:
                p2p_status["friendUpnpInformation"] = friendUpnpStatus

                p2p_status["general_clientConnectionMessage"] = "Friend has UPnP support! Estabilishing connection..."
                p2p_upnpConnectToServer()

    else:
        friends_updateUPnPStatus(True, False, 0)

        success, connectionPort = upnp_newPortForwardingRule(friends_getLocalIP())
        p2p_status["externalConnectionPort"] = connectionPort
        p2p_status["localConnectionPort"] = connectionPort

        if not success:
            p2p_status["general_clientConnectionMessage"] = "Failed to UPnP port forward."
            friends_updateUPnPStatus(False, False, 0)
            return 10

        print("SETTING STATUS TO", connectionPort, "AND")
        friends_updateUPnPStatus(True, False, connectionPort)

        p2p_status["general_clientConnectionMessage"] = "UPnP port forwarding successful! Checking in with friend..."

        while True:
            result = friends_getUPnPStatus(p2p_status["general_currentFocusedFriend"])
            print("On UPnP connection, result is: ", result)

            if result["hasSupport"] == False:
                p2p_status["general_clientConnectionMessage"] = "Friend does not have UPnP support, but we do! Estabilishing connection!"
                p2p_upnpHostServer()


#####################################################
######## P2P FUNCTIONS ##############################
#####################################################

def p2p_forwardToMiddleware(message):
    global p2p_status

    try:
        response = requests.post(
            f"http://localhost:{p2p_status['general_localMiddlewarePort']}/pubEndpoint_receiveMessage",
            data={"message": message}
        )

        if response.status_code != 200:
            print("Failed to forward message to local middleware.")
    except Exception as e:
        print(f"Error receiving P2P message: {e}")


def p2p_handleReceivedMessage(conn):
    global p2p_status

    while True:
        data = conn.recv(1024)
        if not data:
            break

        print("RECEIVED LOCAL NETWORK MESSAGE: ", data.decode('utf-8'))

        if data.decode('utf-8') == "exit":
            return 0
        
        p2p_forwardToMiddleware(data.decode('utf-8'))


def p2p_sendMessageToFriend(message):
    global p2p_status

    friendSocket = p2p_status["directConnectionSocket"]
    friendSocket.sendall(message.encode('utf-8'))


def p2p_localNetworkHostServer():
    global p2p_status

    localSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    localConnectionPort = p2p_findLocallyAvailablePort()
    friends_setLocalNetworkPort(localConnectionPort)
    p2p_status["localConnectionPort"] = localConnectionPort

    print(f"Hosting server on port {localConnectionPort}")

    localSocket.bind(('0.0.0.0', localConnectionPort))
    localSocket.listen(1)

    conn, addr = localSocket.accept()
    print(f"Connection from {addr}")

    p2p_status["directConnectionSocket"] = conn
    p2p_status["general_clientConnectionMessage"] = "P2P connected to friend on local network!"
    p2p_status["friendConnectionStatus"] = 2

    p2p_handleReceivedMessage(conn)

    p2p_status["general_clientConnectionMessage"] = "Friend exited the chat. Returning to tor..."

    return 0


def p2p_upnpHostServer():
    global p2p_status

    localSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    localConnectionPort = p2p_status["localConnectionPort"]
    friends_setLocalNetworkPort(localConnectionPort)

    print(f"Hosting server on port {localConnectionPort}")

    localSocket.bind(('0.0.0.0', localConnectionPort))
    localSocket.listen(1)

    friends_updateUPnPStatus(True, True, p2p_status["externalConnectionPort"])

    conn, addr = localSocket.accept()
    print(f"Connection from {addr}")

    p2p_status["directConnectionSocket"] = conn
    p2p_status["general_clientConnectionMessage"] = "P2P connected to friend with UPnP!"
    p2p_status["friendConnectionStatus"] = 3

    p2p_handleReceivedMessage(conn)

    p2p_status["general_clientConnectionMessage"] = "Friend exited the chat. Returning to tor..."

    return 0



def p2p_localNetworkConnectToServer():
    global p2p_status

    while True:
        localPort = friends_getLocalConnectionPort(p2p_status["general_currentFocusedFriend"])
        if localPort is not None:
            break

    p2p_status["localConnectionPort"] = localPort

    friendSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    friendSocket.connect((p2p_status["friendLocalAddress"], int(localPort)))

    if friendSocket is None:
        return 1

    p2p_status["directConnectionSocket"] = friendSocket
    p2p_status["general_clientConnectionMessage"] = "P2P connected to friend on local network!"
    p2p_status["friendConnectionStatus"] = 2

    p2p_handleReceivedMessage(friendSocket)

    p2p_status["general_clientConnectionMessage"] = "Friend exited the chat. Returning to tor..."

    return 0


def p2p_upnpConnectToServer():
    global p2p_status

    friendPublicAddress = p2p_status["friendPublicAddress"]
    friendPort = p2p_status["friendUpnpInformation"]["upnpPort"]

    print("Connecting to friend on UPnP port ", friendPort)
    print("Connecting to friend on UPnP address ", friendPublicAddress)

    friendSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    friendSocket.connect((friendPublicAddress, int(friendPort)))

    if friendSocket is None:
        p2p_status["general_clientConnectionMessage"] = "Failed to connect to friend :("
        return 1

    p2p_status["directConnectionSocket"] = friendSocket
    p2p_status["general_clientConnectionMessage"] = "P2P connected to friend with UPnP!"

    p2p_status["friendConnectionStatus"] = 3

    p2p_handleReceivedMessage(friendSocket)

    p2p_status["general_clientConnectionMessage"] = "Friend exited the chat. Returning to tor..."

    return 0
    


def p2p_processFirstContact(address):
    localSocksPort = p2p_status["general_socksPort"]

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
    global p2p_status

    result = friends_receiveGenericFriendRequest(request_object_json, "isFocused")

    if result is not True:
        return result

    origin = json.loads(json.loads(request_object_json)["request"])["origin"]

    if p2p_status["general_currentFocusedFriend"] == origin:
        return {"message": "Success", "isFocused": True}
    else:
        return {"message": "Success", "isFocused": False}


def p2p_checkIfIsFocusedFriend(address):
    global p2p_status

    if p2p_status["general_currentFocusedFriend"] == address:
        return {"status": "Focused"}
    else:
        return {"status": "Not focused"}


def p2p_changeFocusedFriend(address):
    global p2p_status

    if address == "null":
        p2p_status["general_currentFocusedFriend"] = None
    else:
        p2p_status["general_currentFocusedFriend"] = address

    return {"status": "Success"}


# for local network connections
def p2p_getLocalConnectionPort():
    global p2p_status

    return p2p_status["localConnectionPort"]



def p2p_getStatusIndicatorBadge():
    global p2p_status

    if p2p_status["general_clientConnectionMessage"] is None:
        return {"status": "No friend connection status available."}

    return {"status": p2p_status["general_clientConnectionMessage"]}


# 0 = not connected
# 1 = connected on localhost
# 2 = connected on local network
# 3 = connected on p2p
def p2p_getFriendConnectionStatus():
    global p2p_status

    friendConnectionStatus = p2p_status["friendConnectionStatus"]

    if friendConnectionStatus == 0:
        return {"status": "0"}
    
    if friendConnectionStatus == 1:
        return {"status": "1", "localhost_friendMiddlewarePort": p2p_status["localhost_friendMiddlewarePort"]}

    elif friendConnectionStatus == 2 or friendConnectionStatus == 3:
        return {"status": str(friendConnectionStatus)}

    raise RuntimeError("Invalid friend connection status.")


# finds port between 40000 and 60000 that is not in use
def p2p_findLocallyAvailablePort():
    while True:
        port = random.randint(50001, 60000)
        if p2p_portIsOpen(port):
            return port


def p2p_portIsOpen(port: int) -> bool:
    print(f"Checking if port {port} is open.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0