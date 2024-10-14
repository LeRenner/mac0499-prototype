import json
import flask
import datetime
import hashlib

from .serverCrypto import *
from .friendRequests import *
from .p2p import *


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
    pubKey = parsedMessageContainer["public_key"]
    localPubKey = getPublicKeyFromAddress(sender)

    # check if the public key is the same as the one in storage.json
    if pubKey != localPubKey:
        return json.dumps({"message": "Invalid public key."})
    
    knownSender = True
    if localPubKey is None:
        knownSender = False
    
    if knownSender:
        if not verifyMessage(parsedMessageContainer["message"], signature, sender):
            return json.dumps({"message": "Invalid signature."})

    # Store the message in storage.json
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"receivedMessages": {}, "sentMessages": {}, "friends": [], "peerList": []}

    if "receivedMessages" not in storage:
        storage["receivedMessages"] = {}

    if sender not in storage["receivedMessages"]:
        storage["receivedMessages"][sender] = []

    storage["receivedMessages"][sender].append(parsedMessageContainer)

    with open("storage.json", "w") as f:
        json.dump(storage, f, indent=4)

    print(f"Message received from {sender}: {content}")

    if knownSender:
        print(f"Message signature verified.")
    else:
        print(f"Message signature not verified because the sender is not known.")

    # Calculate SHA256 of the message content
    sha256_hash = hashlib.sha256(content.encode()).hexdigest()

    return json.dumps({"message": "Message received!", "sha256": sha256_hash})


def checkFriendRequest():
    request = flask.request.form.get("request")
    return processCheckFriendRequest(request)


def getFriendIP():
    request = flask.request.form.get("request")
    return getFriendIPHandler(request)


def p2pRequest():
    return p2pRequestHandler()