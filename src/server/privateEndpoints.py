import json
import flask
import hashlib
import requests
import datetime
from time import sleep

global localSocksPort
global address

from .serverCrypto import *
from .jsonOperator import *


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
        "signature": signMessage(packagedMessage)
    }

    packedMessageContainer = json.dumps(messageContainer)

    for i in range(3):
        try:
            response = requests.post(f"http://{destination}/receiveMessage", data={"message": packedMessageContainer}, proxies=proxies, timeout=15)
            if response.status_code == 200:
                response_data = response.json()

                if response_data.get("message") == "processing":
                    return json.dumps({"message": "processing"})

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

    # Create a copy of the message without the sender field
    message_to_store = {key: value for key, value in message.items() if key != "sender"}

    operator_storeSentMessage(json.dumps(message_to_store), destination)

    return json.dumps({"message": "Message sent!"})


def getMessagesFromSender():
    global address

    sender = flask.request.data.decode('utf-8')

    return operator_getMessagesFromSender(sender)


def isKnownPeer():
    sender = flask.request.get_json().get("address")

    return operator_isKnownPeer(sender)


def getLatestMessages():
    return operator_getLatestMessages()


def getAddress():
    result = {
        "address": address
    }
    return json.dumps(result)


def getSenders():
    return operator_getSenders()


def getFriends():
    return operator_getFriends()


def updatePublicKeyRecords(peerAddress: str) -> bool:
    global localSocksPort

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    for attempt in range(3):
        try:
            print("Starting request...")
            response = requests.get(f"http://{peerAddress}/getPublicKeyBase64", proxies=proxies, timeout=15)

            print(response.json())

            public_key_base64 = response.json().get("public_key")

            print(f"Fetched public key from {peerAddress}: {public_key_base64}")

            operator_storePeerPublicKey(peerAddress, public_key_base64)

            return True
        except requests.RequestException as e:
            print(f"Error fetching public key: {e}")
            if attempt < 2:
                print("Retrying in 5 seconds...")
                sleep(5)
            else:
                print("Failed to fetch public key after three attempts.")
                return False


def startChat():
    friend_address = flask.request.get_json().get("address")

    if operator_getPublicKeyFromAddress(friend_address) is None:
        if not updatePublicKeyRecords(friend_address):
            return json.dumps({"error": "Failed to fetch public key!"})
        else:
            return json.dumps({"message": "Public key fetched!"})
    else:
        return json.dumps({"message": "Public key already in storage!"})


def addFriend():
    friend = flask.request.get_json()

    return operator_addFriend(friend)


def removeFriend():
    friend = flask.request.get_json()

    return operator_removeFriend(friend)


def webInterface(filename):
    if filename == "":
        filename = "index.html"

    return flask.send_from_directory("../web", filename)