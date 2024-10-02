import flask
import logging
import requests
import json
import datetime
import hashlib
from time import sleep

global localHttpPort
global localSocksPort
global address

#############################################################
######## ENDPOINTS ##########################################
#############################################################


def root():
    return "Hello, world!"


def receiveMessage():
    # get the message from the post request
    message = flask.request.form.get("message")
    print(f"Received message: {message}")

    decodedMessage = json.loads(message)
    sender = decodedMessage["sender"].replace("\n", "")
    content = decodedMessage["content"]

    message = {
        "content": content,
        "timestamp": int(datetime.datetime.now().timestamp())
    }

    # Store the message in storage.json
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"receivedMessages": {}, "sentMessages": {}}

    if "receivedMessages" not in storage:
        storage["receivedMessages"] = {}

    if sender not in storage["receivedMessages"]:
        storage["receivedMessages"][sender] = []

    storage["receivedMessages"][sender].append(message)

    with open("storage.json", "w") as f:
        json.dump(storage, f, indent=4)

    print(f"Message received from {sender}: {content}")

    # Calculate SHA256 of the message content
    sha256_hash = hashlib.sha256(content.encode()).hexdigest()

    return json.dumps({"message": "Message received!", "sha256": sha256_hash})


def sendMessage():
    global localSocksPort
    global address

    # get message and address from the post request
    decodedMessage = flask.request.get_json()

    print(f"Decoded message: {decodedMessage}")

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

    print("Destination: ", destination)
    print("Proxies: ", proxies)
    print("Message: ", packagedMessage)

    for i in range(3):
        if 1:
            response = requests.post(f"http://{destination}/receiveMessage", data={"message": packagedMessage}, proxies=proxies)
            if response.status_code == 200:
                response_data = response.json()
                received_sha256 = response_data.get("sha256")
                calculated_sha256 = hashlib.sha256(messageContent.encode()).hexdigest()
                if received_sha256 == calculated_sha256:
                    print("Message sent and verified successfully!")
                    break
                else:
                    print("SHA256 mismatch! Message verification failed.")
            else:
                print(f"Erro ao enviar mensagem: {response.text}")
                return json.dumps({"error": "Error sending message!"})
        # except requests.exceptions.ConnectionError:
        #     print(f"Erro. Tentando novamente em 5 segundos...")
        #     sleep(5)
        #     continue
    else:
        return json.dumps({"error": "Error sending message after multiple attempts!"})

    # Store the message in storage.json
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"receivedMessages": {}, "sentMessages": {}}

    if "sentMessages" not in storage:
        storage["sentMessages"] = {}

    if destination not in storage["sentMessages"]:
        storage["sentMessages"][destination] = []

    # Create a copy of the message without the sender field
    message_to_store = {key: value for key, value in message.items() if key != "sender"}

    storage["sentMessages"][destination].append(message_to_store)

    with open("storage.json", "w") as f:
        json.dump(storage, f, indent=4)

    return json.dumps({"message": "Message sent!"})


def getMessagesFromSender():
    sender = flask.request.data.decode('utf-8')

    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        return json.dumps({"receivedMessages": [], "sentMessages": []})

    receivedMessages = storage.get("receivedMessages", {}).get(sender, [])
    sentMessages = storage.get("sentMessages", {}).get(sender, [])

    # Add sender field to each received message
    for message in receivedMessages:
        message["sender"] = sender

    # Add sender field to each sent message
    for message in sentMessages:
        message["sender"] = address

    # Sort messages by timestamp
    receivedMessages.sort(key=lambda msg: msg["timestamp"])
    sentMessages.sort(key=lambda msg: msg["timestamp"])

    response = {
        "receivedMessages": receivedMessages,
        "sentMessages": sentMessages
    }

    print(f"Messages from {sender}: {response}")

    return json.dumps(response)

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
            latest_message = max(messages, key=lambda msg: msg["timestamp"])
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
    return json.dumps({"address": address})


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


def addFriend():
    friend = flask.request.get_json()

    print(friend)

    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"friends": []}

    friends = storage.get("friends", [])
    if not any(f["address"] == friend["address"] for f in friends):
        friends.append(friend)
        storage["friends"] = friends

        with open("storage.json", "w") as f:
            json.dump(storage, f, indent=4)

        return json.dumps({"message": "Friend added!"})
    else:
        return json.dumps({"message": "Friend already exists!"})


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

    return flask.send_from_directory("web", filename)


#############################################################
######## INITIALIZE SERVER ##################################
#############################################################

def initializeFlask():
    app = flask.Flask(__name__)

    # Set up logging to a file for Flask
    handler = logging.FileHandler('logs/flask.log')
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    return app


def setupEndpoints(app, address, localSocksPort):
    app.add_url_rule("/", "root", root)
    app.add_url_rule("/receiveMessage", "receiveMessage", receiveMessage, methods=["POST"])
    app.add_url_rule("/getMessagesFromSender", "getMessagesFromSender", getMessagesFromSender, methods=["POST"])
    app.add_url_rule("/sendMessage", "sendMessage", sendMessage, methods=["POST"])
    app.add_url_rule("/getLatestMessages", "getLatestMessages", getLatestMessages)
    app.add_url_rule("/getSenders", "getSenders", getSenders)
    app.add_url_rule("/getAddress", "getAddress", getAddress)
    app.add_url_rule("/getFriends", "getFriends", getFriends)
    app.add_url_rule("/addFriend", "addFriend", addFriend, methods=["POST"])
    app.add_url_rule("/removeFriend", "removeFriend", removeFriend, methods=["POST"])
    app.add_url_rule("/web", "webInterface", webInterface, defaults={'filename': ''})
    app.add_url_rule("/web/", "webInterface", webInterface, defaults={'filename': ''})
    app.add_url_rule("/web/<path:filename>", "webInterface", webInterface)


def runServer(argAddress, argHttpPort, argSocksPort):
    global localHttpPort
    global localSocksPort
    global address

    localHttpPort = argHttpPort
    localSocksPort = argSocksPort
    address = argAddress

    app = initializeFlask()
    setupEndpoints(app, address, localSocksPort)
    app.run(host="localhost", port=localHttpPort)
