import flask
import requests
import json
import base64
import datetime
import socket
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
        "shouldKillConnectionThread": False,
        "socksPort": rcvSocksPort,
        "localMiddlewarePort": rcvLocalMiddlewarePort,
        "focusedFriend": None,

        # status message that is shown in the client
        "connectionStatus": None,

        # 0 = not connected
        # 1 = connected on localhost
        # 2 = connected on local network
        # 3 = connected on p2p
        "friendConnectionStatus": 0,

        # for connections on localhost; friend's middleware port        
        "middlewarePort": None,

        # friend's addresses
        "friendPublicAddress": None,
        "friendLocalAddress": None,

        # for local network connections
        "localConnectionPort": None,

        "localNetworkSocket": None,

        "friendUpdateThread": threading.Thread(target=p2p_friendUpdateThread),

        "friendConnectionThread": None
    }
    p2p_status["friendUpdateThread"].start()


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

    p2p_status["shouldKillConnectionThread"] = False
    return -1


def p2p_tryConnecting():
    global p2p_status

    if p2p_status["focusedFriend"] == "00000000000000000000000000000000000000000000000000000000.onion":
        p2p_status["connectionStatus"] = "None."
        return -1

    # check if connection thread should die
    if p2p_status["shouldKillConnectionThread"]: return p2p_connectionThreadDying()

    p2p_status["connectionStatus"] = "Checking if friend is mutual..."

    focusedFriendIsMutual = friends_checkIsMutualFriend(p2p_status["focusedFriend"])

    # check if connection thread should die
    if p2p_status["shouldKillConnectionThread"]: return p2p_connectionThreadDying()

    if focusedFriendIsMutual == False:
        print("Friend is not mutual.")
        p2p_status["connectionStatus"] = "Friend is not mutual."
        return 20

    p2p_status["connectionStatus"] = "Waiting for friend to focus on you..."

    while friends_checkIsFocusedFriend(p2p_status["focusedFriend"]) == False:
        # check if connection thread should die
        if p2p_status["shouldKillConnectionThread"]: return p2p_connectionThreadDying()

        print(".", end="")
        sleep(5)
    

    # check if connection thread should die
    if p2p_status["shouldKillConnectionThread"]: return p2p_connectionThreadDying()


    p2p_status["connectionStatus"] = "Getting friend's IP addresses..."

    friendIPs = friends_getFriendIpAddress(p2p_status["focusedFriend"])

    # check if connection thread should die
    if p2p_status["shouldKillConnectionThread"]: return p2p_connectionThreadDying()

    p2p_status["middlewarePort"] = friendIPs["middlewarePort"]
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
        print("Started! p2p_status[focusedFriend]: ", p2p_status["focusedFriend"])
        print("pastFocusedFriend: ", pastFocusedFriend)

        while p2p_status["focusedFriend"] == pastFocusedFriend:
            sleep(1)

        print("Focused friend changed. Updating connection thread.")
        
        pastFocusedFriend = p2p_status["focusedFriend"]

        if p2p_status["focusedFriend"] is None or "00000000000000000000000000000000000000000" in p2p_status["focusedFriend"]:
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
    p2p_status["connectionStatus"] = "Connected on localhost!"

    while True:
        # check if connection thread should die
        if p2p_status["shouldKillConnectionThread"]: return p2p_connectionThreadDying()

        try:
            requestMethod = {
                "hostname": f"http://localhost:{friendConnectionDetails['middlewarePort']}/pubEndpoint_receiveGenericFriendRequest",
                "proxy": None
            }
            isFocused = friends_checkIsFocusedFriend(p2p_status["focusedFriend"], requestMethod)

            if isFocused == False:
                p2p_status["connectionStatus"] = "Friend closed chat with you. Defaulting to tor."
                return 1
        except requests.RequestException:
            p2p_status["connectionStatus"] = "Friend connection lost."
            return 1
                
        sleep(1)


def p2p_localNetworkConnection():
    global p2p_status

    friendConnectionStatus = 2
    p2p_status["connectionStatus"] = "Connecting on local network..."

    # Determine which peer will host the connection
    if crypto_getOwnAddress() > p2p_status["focusedFriend"]:
        return p2p_hostServer()
    else:
        return p2p_connectToServer()

    return


def p2p_UPnPConnection():
    global p2p_status

    friendConnectionStatus = 3
    p2p_status["connectionStatus"] = "On different networks! Will try to UPNP port forward."

    # try to UPNP port forward
    hasUPnP = upnp_discoverUPnPDevices()

    if hasUPnP == False:
        p2p_status["connectionStatus"] = "No UPnP devices found."
        friends_updateUPnPStatus(False, 0)

        # check if friend has UPnP
        while friends_getUPnPStatus(p2p_status["focusedFriend"]) == None:
            print("Waiting for friend to check UPnP status.")
            sleep(5)
    else:
        success, externalport = upnp_newPortForwardingRule(p2p_getPublicIP(), p2p_status["middlewarePort"])

        if not success:
            p2p_status["connectionStatus"] = "Failed to UPnP port forward."
            friends_updateUPnPStatus(False, 0)
            return 10

        friends_updateUPnPStatus(True, externalport)

        p2p_status["connectionStatus"] = "UPnP port forwarding successful! Checking in with friend..."

        while True:
            result = friends_getUPnPStatus(p2p_status["focusedFriend"])
            print("On UPnP connection, result is: ", result)
            console.log(result)


#####################################################
######## P2P FUNCTIONS ##############################
#####################################################

def p2p_forwardToMiddleware(message):
    global p2p_status

    try:
        response = requests.post(
            f"http://localhost:{p2p_status['localMiddlewarePort']}/pubEndpoint_receiveMessage",
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
        p2p_forwardToMiddleware(data.decode('utf-8'))


def p2p_sendMessageToFriend(message):
    global p2p_status

    friendSocket = p2p_status["localNetworkSocket"]
    friendSocket.sendall(message.encode('utf-8'))


def p2p_hostServer():
    global p2p_status

    localSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sleep(1)

    localConnectionPort = p2p_findLocallyAvailablePort()
    friends_setLocalNetworkPort(localConnectionPort)
    p2p_status["localConnectionPort"] = localConnectionPort

    print(f"Hosting server on port {localConnectionPort}")

    localSocket.bind(('0.0.0.0', localConnectionPort))
    localSocket.listen(1)

    conn, addr = localSocket.accept()
    print(f"Connection from {addr}")

    p2p_status["localNetworkSocket"] = conn

    p2p_status["friendConnectionStatus"] = 2

    p2p_handleReceivedMessage(conn)

    return 0


def p2p_connectToServer():
    global p2p_status

    friendLocalConnectionPort = friends_setLocalNetworkPort(p2p_status["focusedFriend"])
    p2p_status["localConnectionPort"] = friendLocalConnectionPort

    friendSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    friendSocket.connect((p2p_status["friendLocalAddress"], friendLocalConnectionPort))

    p2p_status["localNetworkSocket"] = friendSocket

    p2p_status["friendConnectionStatus"] = 2

    p2p_handleReceivedMessage(friendSocket)

    return 0


def p2p_processFirstContact(address):
    localSocksPort = p2p_status["socksPort"]

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

    if p2p_status["focusedFriend"] == origin:
        return {"message": "Success", "isFocused": True}
    else:
        return {"message": "Success", "isFocused": False}


def p2p_checkIfIsFocusedFriend(address):
    global p2p_status

    if p2p_status["focusedFriend"] == address:
        return {"status": "Focused"}
    else:
        return {"status": "Not focused"}


def p2p_changeFocusedFriend(address):
    global p2p_status

    if address == "null":
        p2p_status["focusedFriend"] = None
    else:
        p2p_status["focusedFriend"] = address

    return {"status": "Success"}


# for local network connections
def p2p_getLocalConnectionPort():
    global p2p_status

    return p2p_status["localConnectionPort"]



def p2p_getStatusIndicatorBadge():
    global p2p_status

    print("Status indicator badge: ", p2p_status["connectionStatus"])

    if p2p_status["connectionStatus"] is None:
        return {"status": "No friend connection status available."}

    return {"status": p2p_status["connectionStatus"]}


# 0 = not connected
# 1 = connected on localhost
# 2 = connected on local network
# 3 = connected on p2p
def p2p_getFriendConnectionStatus():
    global p2p_status

    if friendConnectionStatus == 0:
        return {"status": "0"}
    
    if friendConnectionStatus == 1:
        return {"status": "1", "middlewarePort": p2p_status["middlewarePort"]}

    return friendConnectionStatus


# finds port between 40000 and 60000 that is not in use
def p2p_findLocallyAvailablePort():
    for i in range(40000, 60000):
        if p2p_portIsOpen(i):
            return i

    return -1


def p2p_portIsOpen(port: int) -> bool:
    print(f"Checking if port {port} is open.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0
