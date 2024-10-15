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

global currentFocusedFriend
global friendConnectionThread
global friendUpdateThread
global localSocksPort
global friendConnectionStatus


def p2p_initializeVariables(rcvSocksPort):
    global friendConnectionThread
    global friendUpdateThread
    global localSocksPort

    localSocksPort = rcvSocksPort
    currentFocusedFriend = None
    friendConnectionStatus = None
    friendConnectionThread = threading.Thread(target=p2p_friendConnectionThread)
    friendConnectionThread.start()
    friendUpdateThread = threading.Thread(target=p2p_friendUpdateThread)
    friendUpdateThread.start()


#####################################################
######## P2P THREADS ################################
#####################################################

def p2p_friendConnectionThread():
    global currentFocusedFriend
    global friendConnectionStatus

    friendConnectionStatus = "Checking if friend is mutual..."

    focusedFriendIsMutual = friends_checkIsMutualFriend(currentFocusedFriend)

    friendConnectionStatus = "Getting friend's IP addresses..."
    


def p2p_friendUpdateThread():
    global currentFocusedFriend
    global friendConnectionThread

    pastFocusedFriend = None

    while True:
        while currentFocusedFriend == pastFocusedFriend:
            sleep(1)
        
        pastFocusedFriend = currentFocusedFriend

        if currentFocusedFriend is None:
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


def p2p_getLocalIP():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip


def p2p_changeFocusedFriend(address):
    global currentFocusedFriend

    if address == "null":
        currentFocusedFriend = None
    else:
        currentFocusedFriend = address


def p2p_getFriendConnectionStatus():
    global friendConnectionStatus
    return friendConnectionStatus