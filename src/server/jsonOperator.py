import json
import time
import random
import threading


class WriteLock:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_locked = False

    def acquire(self):
        self.lock.acquire()
        self.is_locked = True

    def release(self):
        self.is_locked = False
        self.lock.release()


global writeLock
global defaultStorage
writeLock = WriteLock()
defaultStorage = {"receivedMessages": {}, "sentMessages": {}, "friends": [], "peerList": [], "firstContact": []}


def operator_getCurrentStorage():
    global writeLock
    global defaultStorage

    writeLock.acquire()

    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = defaultStorage

    return storage


def operator_checkFirstContact(address: str):
    global writeLock
    storage = operator_getCurrentStorage()
    writeLock.release()

    if "firstContact" not in storage:
        return None

    for contact in storage["firstContact"]:
        if contact["address"] == address:
            return contact["success"]

    return None


def operator_successFirstContact(address: str):
    global writeLock
    storage = operator_getCurrentStorage()

    if "firstContact" not in storage:
        writeLock.release()
        return

    for contact in storage["firstContact"]:
        if contact["address"] == address:
            contact["success"] = True

    with open("storage.json", "w") as f:
        json.dump(storage, f)
    
    writeLock.release()
    return


def operator_removeFirstContact(address: str):
    global writeLock
    storage = operator_getCurrentStorage()

    if "firstContact" not in storage:
        writeLock.release()
        return

    for contact in storage["firstContact"]:
        if contact["address"] == address:
            storage["firstContact"].remove(contact)

    with open("storage.json", "w") as f:
        json.dump(storage, f)
    
    writeLock.release()
    return


def operator_addFirstContact(address: str, success: bool = False):
    global writeLock
    storage = operator_getCurrentStorage()

    if "firstContact" not in storage:
        storage["firstContact"] = []

    firstContactObj = {
        "address": address,
        "success": success,
    }

    storage["firstContact"].append(firstContactObj)

    with open("storage.json", "w") as f:
        json.dump(storage, f)
    
    writeLock.release()
    return


def operator_storeReceivedMessage(message: str):
    global writeLock
    storage = operator_getCurrentStorage()

    parsedMessageContainer = json.loads(message)
    parsedMessage = json.loads(parsedMessageContainer["message"])

    sender = parsedMessage["sender"].replace("\n", "")

    parsedMessage["sender"] = sender
    parsedMessageContainer["message"] = json.dumps(parsedMessage)

    if "receivedMessages" not in storage:
        storage["receivedMessages"] = []
    
    if sender not in storage["receivedMessages"]:
        storage["receivedMessages"][sender] = []
    
    storage["receivedMessages"][sender].append(parsedMessageContainer)

    with open("storage.json", "w") as f:
        json.dump(storage, f)
    
    writeLock.release()
    return


def operator_storeSentMessage(message: str):
    global writeLock
    storage = operator_getCurrentStorage()

    parsedMessageContainer = json.loads(message)
    parsedMessage = json.loads(parsedMessageContainer["message"])

    destination = parsedMessage["destination"].replace("\n", "")

    parsedMessage["destination"] = destination
    parsedMessageContainer["message"] = json.dumps(parsedMessage)

    if "sentMessages" not in storage:
        storage["sentMessages"] = []
    
    if destination not in storage["sentMessages"]:
        storage["sentMessages"][destination] = []
    
    storage["sentMessages"][destination].append(parsedMessageContainer)

    with open("storage.json", "w") as f:
        json.dump(storage, f)
    
    writeLock.release()
    return
    

def operator_storePeerPublicKey(address: str, publicKey: str):
    global writeLock
    storage = operator_getCurrentStorage()

    if "peerList" not in storage:
        storage["peerList"] = []

    peerObj = {
        "address": address,
        "public_key": publicKey
    }

    for peer in storage["peerList"]:
        if peer["address"] == address:
            writeLock.release()
            return  # Peer already exists, do not add again

    storage["peerList"].append(peerObj)

    with open("storage.json", "w") as f:
        json.dump(storage, f)
    
    writeLock.release()
    return


def operator_getMessagesFromSender(sender: str):
    global writeLock
    storage = operator_getCurrentStorage()
    writeLock.release()

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


def operator_isKnownPeer(address: str):
    global writeLock
    storage = operator_getCurrentStorage()
    writeLock.release()

    knownPeers = storage.get("knownPeers", [])

    if any(f["address"] == sender for f in knownPeers):
        writeLock.release()
        return json.dumps({"verified": True})
    else:
        return json.dumps({"verified": False})


def operator_getLatestMessages():
    global writeLock
    storage = operator_getCurrentStorage()
    writeLock.release()

    receivedMessages = storage.get("receivedMessages", {})
    sentMessages = storage.get("sentMessages", {})
    latestMessages = {}

    # Get the latest received messages
    for sender, messages in receivedMessages.items():
        if messages:
            latest_message = json.loads(messages[-1]["message"])

            for message in messages:
                parsedMessage = json.loads(message["message"])
                print("Parsed message: ", parsedMessage)
                if parsedMessage["timestamp"] > latest_message["timestamp"]:
                    latest_message = message

            latest_message_with_sender = latest_message.copy()
            latest_message_with_sender["sender"] = sender
            latestMessages[sender] = latest_message_with_sender
            print("Current latest messages: ", latestMessages)

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


def operator_getSenders():
    global writeLock
    storage = operator_getCurrentStorage()
    writeLock.release()

    receivedMessages = storage.get("receivedMessages", {})
    senders = list(receivedMessages.keys())

    return json.dumps(senders)


def operator_getFriends():
    global writeLock
    storage = operator_getCurrentStorage()
    writeLock.release()

    friends = storage.get("friends", [])

    return json.dumps(friends)


def operator_addFriend(address: str):
    global writeLock
    storage = operator_getCurrentStorage()
    
    friends = storage.get("friends", [])

    if any(f["address"] == friend["address"] for f in friends):
        writeLock.release()
        return json.dumps({"message": "Friend already added!"})
    
    friends.append(friend)
    storage["friends"] = friends

    with open("storage.json", "w") as f:
        json.dump(storage, f, indent=4)
    
    writeLock.release()
    return json.dumps({"message": "Friend added!"})


def operator_removeFriend(address: str):
    global writeLock
    storage = operator_getCurrentStorage()
    
    friends = storage.get("friends", [])

    for friend in friends:
        if friend["address"] == address:
            friends.remove(friend)
            storage["friends"] = friends

            with open("storage.json", "w") as f:
                json.dump(storage, f, indent=4)
            
            writeLock.release()
            return json.dumps({"message": "Friend removed!"})
    
    writeLock.release()
    return json.dumps({"message": "Friend not found!"})


def getPublicKeyFromAddress(address: str) -> str:
    # open storage.json and get key peerList
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"peerList": []}
    
    peerList = storage.get("peerList", [])

    for peer in peerList:
        if peer["address"] == address:
            return peer["public_key"]
    
    return None