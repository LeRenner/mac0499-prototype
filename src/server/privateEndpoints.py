import json
import flask
import hashlib
import requests
import datetime
from time import sleep

from .serverCrypto import *
from .jsonOperator import *
from .p2p import *

global localSocksPort
global address

def privEndpoint_setupPrivateEndpointVariables(argAddress, argLocalSocksPort):
    global localSocksPort
    global address

    localSocksPort = argLocalSocksPort
    address = argAddress


#############################################################
######## PRIVATE ENDPOINTS ##################################
#############################################################


def privEndpoint_sendMessage():
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

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    hostname = f"http://{destination}/pubEndpoint_receiveMessage"

    messageContainer = {
        "message": packagedMessage,
        "signature": crypto_signMessage(packagedMessage)
    }

    packedMessageContainer = json.dumps(messageContainer)

    # check is message can be sent locally
    if p2p_getFriendConnectionStatus()["status"] == "1":
        print("ARRIVED HERE")

        middlewarePort = p2p_getFriendConnectionStatus()["localhost_friendMiddlewarePort"]

        print("Middleware port is", middlewarePort)

        hostname = f"http://localhost:{middlewarePort}/pubEndpoint_receiveMessage"
        proxies = None
    

    if p2p_getFriendConnectionStatus()["status"] == "2" or p2p_getFriendConnectionStatus()["status"] == "3":
        p2p_sendMessageToFriend(packedMessageContainer, destination)
        message_to_store = {key: value for key, value in message.items() if key != "sender"}
        operator_storeSentMessage(json.dumps(message_to_store), destination)
        return json.dumps({"message": "Message sent!"})
    

    print("Sending message to", hostname, "with content", messageContent, "and proxies", proxies)

    success = False
    for i in range(3):
        try:
            response = requests.post(hostname, data={"message": packedMessageContainer}, proxies=proxies, timeout=15)
            if response.status_code == 200:
                response_data = response.json()

                if response_data.get("message") == "processing":
                    return json.dumps({"message": "processing"})

                received_sha256 = response_data.get("sha256")
                calculated_sha256 = hashlib.sha256(messageContent.encode()).hexdigest()
                if received_sha256 == calculated_sha256:
                    print("Message sent successfully!")
                    success = True
                    break
                else:
                    print("SHA256 mismatch! Message verification failed.")
                    continue
            else:
                print(f"Erro. Tentando novamente em 5 segundos...")
                sleep(5)
                continue
        except requests.RequestException as e:
            print(f"Erro: {e}. Tentando novamente em 5 segundos...")
            sleep(5)
            continue
    else:
        return json.dumps({"error": "Failed to send message after three tries!"})

    if not success:
        return json.dumps({"error": "Failed to send message after three tries!"})

    # Create a copy of the message without the sender field
    message_to_store = {key: value for key, value in message.items() if key != "sender"}

    operator_storeSentMessage(json.dumps(message_to_store), destination)

    return json.dumps({"message": "Message sent!"})


def privEndpoint_getMessagesFromSender():
    global address

    sender = flask.request.data.decode('utf-8')

    return operator_getMessagesFromSender(sender)


def privEndpoint_isKnownPeer():
    sender = flask.request.get_json().get("address")

    return operator_isKnownPeer(sender)


def privEndpoint_getLatestMessages():
    return operator_getLatestMessages()


def privEndpoint_getAddress():
    result = {
        "address": address
    }
    return json.dumps(result)


def privEndpoint_getSenders():
    return operator_getSenders()


def privEndpoint_getFriends():
    friends = operator_getFriends()

    response = {
        "friends": friends
    }
    
    return json.dumps(response)


def privEndpoint_updatePublicKeyRecords(peerAddress: str) -> bool:
    global localSocksPort

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    for attempt in range(3):
        try:
            print("[updatePublicKeyRecords] Starting request to:", f"http://{peerAddress}/pubEndpoint_getPublicKeyBase64", "with proxies", proxies)
            response = requests.get(f"http://{peerAddress}/pubEndpoint_getPublicKeyBase64", proxies=proxies, timeout=15)

            public_key_base64 = response.json().get("public_key")

            print(f"[updatePublicKeyRecords] Fetched pubkey: {public_key_base64}")

            operator_storePeerPublicKey(peerAddress, public_key_base64)

            return True
        except requests.RequestException as e:
            print(f"Error fetching public key")
            if attempt < 2:
                print("Retrying in 5 seconds...")
                sleep(5)
            else:
                print("Failed to fetch public key after three attempts.")
                return False


def privEndpoint_startChat():
    friend_address = flask.request.get_json().get("address")

    if operator_getPublicKeyFromAddress(friend_address) is None:
        if not privEndpoint_updatePublicKeyRecords(friend_address):
            return json.dumps({"error": "Failed to fetch public key!"})
        else:
            return json.dumps({"message": "Public key fetched!"})
    else:
        return json.dumps({"message": "Public key already in storage!"})


def privEndpoint_addFriend():
    friend = flask.request.get_json()

    return operator_addFriend(friend)


def privEndpoint_removeFriend():
    friend = flask.request.get_json()

    return operator_removeFriend(friend["alias"])


def privEndpoint_webInterface(filename):
    if filename == "":
        filename = "index.html"

    return flask.send_from_directory("../web", filename)


def privEndpoint_changeFocusedFriend():
    friend = flask.request.get_json().get("address")

    print("Changing focused friend to", friend)

    return p2p_changeFocusedFriend(friend)


def privEndpoint_getFriendConectionStatus():
    return p2p_getStatusIndicatorBadge()