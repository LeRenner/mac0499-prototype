import json
import flask
import hashlib
import requests
import datetime
from time import sleep

global localSocksPort
global address

from .serverCrypto import *


def setupPrivateEndpointVariables(argAddress, argLocalSocksPort):
    global localSocksPort
    global address

    localSocksPort = argLocalSocksPort
    address = argAddress


#############################################################
######## PRIVATE ENDPOINTS ##################################
#############################################################


def sendMessage():
    global localSocksPort
    global address

    # get message and address from the post request
    decodedMessage = flask.request.get_json()

    destination = decodedMessage["address"]
    messageContent = decodedMessage["message"]

    message = {
        "sender": address,
        "content": messageContent,
        "timestamp": int(datetime.datetime.now().timestamp())
    }

    packagedMessage = json.dumps(message)

    print(f"Enviando mensagem para {destination}...")
    # send the message to the server

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    messageContainer = {
        "message": packagedMessage,
        "signature": signMessage(packagedMessage),
        "public_key": getOwnPublicKey()
    }

    packedMessageContainer = json.dumps(messageContainer)

    for i in range(3):
        try:
            response = requests.post(f"http://{destination}/receiveMessage", data={"message": packedMessageContainer}, proxies=proxies)
            if response.status_code == 200:
                response_data = response.json()
                received_sha256 = response_data.get("sha256")
                calculated_sha256 = hashlib.sha256(messageContent.encode()).hexdigest()
                if received_sha256 == calculated_sha256:
                    break
                else:
                    print("SHA256 mismatch! Message verification failed.")
                    continue
            else:
                print(f"Erro. Tentando novamente em 5 segundos...")
                sleep(5)
                continue
        except requests.exceptions.ConnectionError:
            print(f"Erro. Tentando novamente em 5 segundos...")
            sleep(5)
            continue
    else:
        return json.dumps({"error": "Failed to send message after three tries!"})

    # Store the message in storage.json
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"receivedMessages": {}, "sentMessages": {}, "friends": [], "peerList": []}

    # Create a copy of the message without the sender field
    message_to_store = {key: value for key, value in message.items() if key != "sender"}

    if destination not in storage["receivedMessages"]:
        storage["receivedMessages"][destination] = []

    storage["sentMessages"][destination].append(message_to_store)

    with open("storage.json", "w") as f:
        json.dump(storage, f, indent=4)

    return json.dumps({"message": "Message sent!"})


def getMessagesFromSender():
    global address

    sender = flask.request.data.decode('utf-8')

    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        return json.dumps({"receivedMessages": [], "sentMessages": []})

    receivedMessages = storage.get("receivedMessages", {}).get(sender, [])
    sentMessages = storage.get("sentMessages", {}).get(sender, [])

    # Add sender field to each received message
    parsedReceivedMessages = []
    for message in receivedMessages:
        parsedMessage = json.loads(message["message"])
        parsedMessage["sender"] = sender
        parsedReceivedMessages.append(parsedMessage)

    # Add sender field to each sent message
    for message in sentMessages:
        message["sender"] = address

    # Sort messages by timestamp
    receivedMessages.sort(key=lambda msg: msg["timestamp"])
    sentMessages.sort(key=lambda msg: msg["timestamp"])

    response = {
        "receivedMessages": parsedReceivedMessages,
        "sentMessages": sentMessages
    }

    return json.dumps(response)


def isVerifiedSender():
    sender = flask.request.get_json().get("address")

    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        return json.dumps({"verified": False})

    knownPeers = storage.get("knownPeers", [])

    if any(f["address"] == sender for f in knownPeers):
        return json.dumps({"verified": True})
    else:
        return json.dumps({"verified": False})


def getLatestMessages():
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        return json.dumps({"messages": []})

    receivedMessages = storage.get("receivedMessages", {})
    sentMessages = storage.get("sentMessages", {})
    latestMessages = {}

    # Get the latest received messages
    for sender, messages in receivedMessages.items():
        if messages:
            latest_message = max(messages, key=lambda msg: json.loads(msg["message"])["timestamp"])
            latest_message_with_sender = latest_message.copy()
            latest_message_with_sender["sender"] = sender
            latestMessages[sender] = latest_message_with_sender

    # Get the latest sent messages
    for recipient, messages in sentMessages.items():
        if messages:
            latest_message = max(messages, key=lambda msg: msg["timestamp"])
            latest_message_with_sender = latest_message.copy()
            latest_message_with_sender["sender"] = recipient  # Use the recipient address
            if recipient not in latestMessages or latest_message_with_sender["timestamp"] > latestMessages[recipient]["timestamp"]:
                latestMessages[recipient] = latest_message_with_sender

    # Convert the dictionary to a list and sort by timestamp
    latestMessagesList = list(latestMessages.values())
    latestMessagesList.sort(key=lambda msg: msg["timestamp"], reverse=True)

    response = {
        "messages": latestMessagesList
    }

    return json.dumps(response)


def getAddress():
    result = {
        "address": address
    }
    return json.dumps(result)


def getSenders():
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        return json.dumps([])

    receivedMessages = storage.get("receivedMessages", {})
    senders = list(receivedMessages.keys())

    return json.dumps(senders)


def getFriends():
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        return json.dumps([])

    friends = storage.get("friends", [])

    return json.dumps(friends)


def startChat():
    ISAHDHIASODHIOHISODHAIOSHOAHSIDOHIAOSHIDOHAIOSHDOAHSIDOHIASHIDHAISHDIOAHOSIDHIAOSHOIHAIOSDIOAHSIDHOAHSOIDHIAOSHIDOHAOISHDIHAIOSHDAIHOSHIOD


def addFriend():
    friend = flask.request.get_json()

    # check if the friend is already a friend
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"friends": []}
    
    friends = storage.get("friends", [])

    if any(f["address"] == friend["address"] for f in friends):
        return json.dumps({"error": "Friend already added!"})
    
    friends.append(friend)
    storage["friends"] = friends

    with open("storage.json", "w") as f:
        json.dump(storage, f, indent=4)

    return json.dumps({"message": "Friend added!"})


def removeFriend():
    friend_nickname = flask.request.get_json().get("alias")

    print(friend_nickname)

    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        return json.dumps({"error": "Friend not found!"})

    friends = storage.get("friends", [])

    print(friends)

    friend_to_remove = next((f for f in friends if f["alias"] == friend_nickname), None)



    if friend_to_remove:
        friends.remove(friend_to_remove)
        storage["friends"] = friends

        with open("storage.json", "w") as f:
            json.dump(storage, f, indent=4)

        return json.dumps({"message": "Friend removed!"})
    else:
        return json.dumps({"error": "Friend not found!"})


def webInterface(filename):
    if filename == "":
        filename = "index.html"

    return flask.send_from_directory("../web", filename)