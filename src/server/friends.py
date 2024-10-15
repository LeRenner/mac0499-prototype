import json
import datetime
import base64
import requests

from .serverCrypto import *
from .jsonOperator import *

global localSocksPort


def friends_initializeVariables(rcvSocksPort):
    global localSocksPort
    localSocksPort = rcvSocksPort


#####################################################
######## FRIEND REQUESTS ############################
#####################################################

def friends_craftFriendCheckRequest(destAddress: str) -> str:
    request = {
        "origin": crypto_getOwnAddress,
        "destination": destAddress,
        "timestamp": int(datetime.datetime.now().timestamp()),
        "kind": "checkFriend"
    }

    # Serialize the request as JSON
    request_json = json.dumps(request)

    # Sign the request
    signature = crypto_signMessage(request_json)

    # Create the final request object
    request_object = {
        "request": request,
        "signature": signature
    }

    # Serialize the request object as JSON
    request_object_json = json.dumps(request_object)

    return request_object_json


def friends_receiveCheckFriendRequest(request_object_json: str) -> bool:
    # Deserialize the request object
    deserialized_request_object = json.loads(request_object_json)

    # Extract the request and signature
    request = deserialized_request_object["request"]
    signature = deserialized_request_object["signature"]

    deserializedRequest = json.loads(request)
    
    origin = deserializedRequest["origin"]
    destination = deserializedRequest["destination"]
    timestamp = deserializedRequest["timestamp"]
    kind = deserializedRequest["kind"]

    if destination != crypto_getOwnAddress():
        return {"error": "Destination address does not match."}
    
    if kind != "checkFriend":
        return {"error": "Invalid kind."}
    
    if not crypto_verifyMessage(request, signature, origin):
        return {"error": "Invalid signature."}
    
    if int(datetime.datetime.now().timestamp()) - timestamp > 120:
        return {"error": "Request is too old."}

    friends = operator_getFriends()
    for friend in friends:
        if friend["address"] == origin:
            return {"friend": True}
    
    return {"friend": False}


def friends_checkIsMutualFriend(friendAddress: str) -> bool:
    global localSocksPort

    iAmTheirFriend = None
    theyAreMyFriend = None

    myFriends = operator_getFriends()
    for friend in myFriends:
        if friend["address"] == friendAddress:
            theyAreMyFriend = True
            break
    if theyAreMyFriend is None:
        theyAreMyFriend = False

    checkFriendRequest = friends_craftFriendCheckRequest(friendAddress)

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    for attempt in range(3):
        try:
            print("[friends_checkIsMutualFriend] Starting request...")
            response = requests.post(f"http://{friendAddress}/pubEndpoint_checkFriendRequest", data=checkFriendRequest, proxies=proxies, timeout=15)

            response_json = response.json()
            iAmTheirFriend = response_json.get("friend")

            if iAmTheirFriend is not None:
                break
        except requests.RequestException as e:
            print(f"Error checking friend status: {e}")
            if attempt < 2:
                print("Retrying in 5 seconds...")
                sleep(5)
            else:
                print("Failed to check friend status after three attempts.")
                iAmTheirFriend = False

    return theyAreMyFriend and iAmTheirFriend



def friends_craftGetIpRequest(destAddress: str) -> str:
    request = {
        "origin": crypto_getOwnAddress,
        "destination": destAddress,
        "timestamp": int(datetime.datetime.now().timestamp()),
        "kind": "getIp"
    }

    # Serialize the request as JSON
    request_json = json.dumps(request)

    # Sign the request
    signature = crypto_signMessage(request_json)

    # Create the final request object
    request_object = {
        "request": request,
        "signature": signature
    }

    # Serialize the request object as JSON
    request_object_json = json.dumps(request_object)

    return request_object_json


def friends_receiveGetIpRequest(request_object_json: str) -> bool:
    # Deserialize the request object
    deserialized_request_object = json.loads(request_object_json)

    # Extract the request and signature
    request = deserialized_request_object["request"]
    signature = deserialized_request_object["signature"]

    deserializedRequest = json.loads(request)
    
    origin = deserializedRequest["origin"]
    destination = deserializedRequest["destination"]
    timestamp = deserializedRequest["timestamp"]
    kind = deserializedRequest["kind"]

    if destination != crypto_getOwnAddress():
        return {"error": "Destination address does not match."}
    
    if kind != "getIp":
        return {"error": "Invalid kind."}
    
    if not crypto_verifyMessage(request, signature, origin):
        return {"error": "Invalid signature."}
    
    if int(datetime.datetime.now().timestamp()) - timestamp > 120:
        return {"error": "Request is too old."}

    friends = operator_getFriends()
    for friend in friends:
        if friend["address"] == origin:
            return {"friend": True}
    
    return {"friend": False}


#####################################################
######## AUXILIARY FUNCTIONS ########################
#####################################################

def friends_getPublicIP():
    try:
        response = requests.get("http://httpbin.org/ip")
        return response.json()["origin"]
    except requests.exceptions.RequestException:
        return None


def friends_getLocalIP():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip