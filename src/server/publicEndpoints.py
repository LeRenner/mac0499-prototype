import json
import flask
import datetime
import hashlib

from .serverCrypto import *
from .jsonOperator import *
from .friends import *
from .p2p import *
import threading
import requests
from time import sleep

global threads
global localSocksPort
threads = []

def pubEndpoint_setupPublicEndpointlVariables(socksPort):
    global localSocksPort
    localSocksPort = socksPort


#############################################################
######## PUBLIC ENDPOINTS ###################################
#############################################################

def pubEndpoint_receiveMessage():
    # get the message from the post request
    message = flask.request.form.get("message")

    parsedMessageContainer = json.loads(message)

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
        thread = threading.Thread(target=p2p_processFirstContact, args=(sender,))
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


def pubEndpoint_getPublicKeyBase64():
    return json.dumps({"public_key": crypto_getOwnPublicKey()})


def pubEndpoint_receiveGenericFriendRequest():
    request_object_json = flask.request.form.get("request")

    request_type = json.loads(json.loads(request_object_json).get("request")).get("kind")

    if request_type == "getIp":
        return json.dumps(friends_receiveGetIpRequest(request_object_json))
    elif request_type == "isFocused":
        return json.dumps(p2p_receiveFriendIsFocusedRequest(request_object_json))
    elif request_type == "checkFriend":
        return json.dumps(friends_receiveCheckFriendRequest(request_object_json))
    elif request_type == "getUPnPStatus":
        return json.dumps(friends_receiveUPnPStatusRequest(request_object_json))
    elif request_type == "getLocalPort":
        return json.dumps(friends_receiveGetLocalConnectionPort(request_object_json))
    else:
        return json.dumps({"message": "Invalid request type."})


def pubEndpoint_ping():
    return json.dumps({"message": "Success"})