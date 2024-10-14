import json
import flask
import datetime
import hashlib

from .serverCrypto import *
from .friendRequests import *
from .jsonOperator import *
from .p2p import *
import threading
import requests
from time import sleep

global threads
global localSocksPort
threads = []

def setupPublicEndpointlVariables(socksPort):
    global localSocksPort
    localSocksPort = socksPort

def processFirstContact(address):
    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    for i in range(3):
        try:
            response = requests.get(f"http://{address}/getPublicKeyBase64", proxies=proxies, timeout=15)
            if response.status_code == 200:
                response_data = response.json()
                public_key = response_data.get("public_key")
                if public_key:
                    operator_storePeerPublicKey(address, public_key)
                    operator_successFirstContact(address)
                    return
        except requests.RequestException as e:
            print(f"Attempt {i+1} failed: {e}")
        sleep(1)

    operator_removeFirstContact(address)
    print("Failed to retrieve public key after 3 attempts.")


#############################################################
######## PUBLIC ENDPOINTS ###################################
#############################################################

def receiveMessage():
    # get the message from the post request
    message = flask.request.form.get("message")

    parsedMessageContainer = json.loads(message)

    print("Parsed message: ", parsedMessageContainer)

    decodedMessage = json.loads(parsedMessageContainer["message"])
    sender = decodedMessage["sender"].replace("\n", "")
    content = decodedMessage["content"]

    message = {
        "content": content,
        "timestamp": int(datetime.datetime.now().timestamp())
    }

    # verify the signature
    signature = parsedMessageContainer["signature"]
    localPubKey = operator_getPublicKeyFromAddress(sender)

    if operator_checkFirstContact(sender) != None:
        # Wait for firstContact object to be successful or to disappear from list
        while operator_checkFirstContact(sender) == False:
            sleep(1)
        
        localPubKey = operator_getPublicKeyFromAddress(sender)
        if localPubKey is None:
            return json.dumps({"message": "Failed to fetch public key from sender."})
    
    if localPubKey is None:
        # Fetch the public key from the sender and add the tor address to firstContact
        operator_addFirstContact(sender)

        # Start a new thread to process the first contact
        thread = threading.Thread(target=processFirstContact, args=(sender,))
        thread.start()
        threads.append(thread)

        return json.dumps({"message": "processing"})

    if localPubKey is not None:
        if not crypto_verifyMessage(parsedMessageContainer["message"], signature, sender):
            return json.dumps({"message": "Invalid signature."})
    else:
        return json.dumps({"message": "Public key not found."})

    # store the message
    operator_storeReceivedMessage(json.dumps(parsedMessageContainer))

    # Calculate SHA256 of the message content
    sha256_hash = hashlib.sha256(content.encode()).hexdigest()

    return json.dumps({"message": "Message received!", "sha256": sha256_hash})


def getPublicKeyBase64():
    return json.dumps({"public_key": crypto_getOwnPublicKey()})

def checkFriendRequest():
    request = flask.request.form.get("request")
    return processCheckFriendRequest(request)


def getFriendIP():
    request = flask.request.form.get("request")
    return getFriendIPHandler(request)


def p2pRequest():
    return p2pRequestHandler()