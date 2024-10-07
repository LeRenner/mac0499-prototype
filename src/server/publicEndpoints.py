import json
import flask
import datetime
import hashlib


#############################################################
######## PUBLIC ENDPOINTS ###################################
#############################################################

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