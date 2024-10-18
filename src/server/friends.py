import json
import datetime
import base64
import requests
import socket
from time import sleep

from .serverCrypto import *
from .jsonOperator import *

global localSocksPort
global localMiddlewarePort
global upnpStatus

def friends_initializeVariables(rcvSocksPort, rcvLocalMiddlewarePort):
    global localSocksPort
    global localMiddlewarePort
    global upnpStatus

    localSocksPort = rcvSocksPort
    localMiddlewarePort = rcvLocalMiddlewarePort

    upnpStatus = {
        "enabled": None,
        "upnpPort": 0
    }


def friends_updateUPnPStatus(upnpEnabled: bool, upnpPort: int = 0):
    global upnpStatus
    upnpStatus["enabled"] = upnpEnabled
    upnpStatus["upnpPort"] = upnpPort


##########################################################################################################
######## FRIEND REQUESTS #################################################################################
##########################################################################################################


#####################################################
######## CRAFT REQUESTS #############################
#####################################################

def friends_craftGenericFriendRequest(destAddress: str, requestKind: str) -> str:
    request = {
        "origin": crypto_getOwnAddress(),
        "destination": destAddress,
        "timestamp": int(datetime.datetime.now().timestamp()),
        "kind": requestKind
    }

    # Serialize the request as JSON
    request_json = json.dumps(request)

    # Sign the request
    signature = crypto_signMessage(request_json)

    # Create the final request object
    request_object = {
        "request": request_json,
        "signature": signature
    }

    # Serialize the request object as JSON
    request_object_json = json.dumps(request_object)

    return request_object_json


#####################################################
######## RECEIVE REQUESTS ###########################
#####################################################

def friends_receiveGenericFriendRequest(request_object_json: str, request_kind) -> bool:
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
    
    if kind != request_kind:
        return {"error": "Invalid kind."}
    
    if not crypto_verifyMessage(request, signature, origin):
        return {"error": "Invalid signature."}
    
    if int(datetime.datetime.now().timestamp()) - timestamp > 120:
        return {"error": "Request is too old."}
    
    if kind != "checkFriend" and not friends_isFriend(origin):
        return {"error": "Origin is not a friend."}
    
    return True


def friends_receiveGetIpRequest(request_object_json: str) -> bool:
    global localMiddlewarePort
    result = friends_receiveGenericFriendRequest(request_object_json, "getIp")

    if result is not True:
        return result

    ownLocalIP = friends_getLocalIP()
    ownPublicIP = friends_getPublicIP()

    return {"message": "Success", "localIp": ownLocalIP, "publicIp": ownPublicIP, "middlewarePort": localMiddlewarePort}


def friends_receiveCheckFriendRequest(request_object_json: str) -> bool:
    result = friends_receiveGenericFriendRequest(request_object_json, "checkFriend")

    if result is not True:
        return result

    origin = json.loads(json.loads(request_object_json)["request"])["origin"]

    if friends_isFriend(origin):
        return {"message": "Success", "friend": True}
    else:
        return {"message": "Success", "friend": False}


def friends_receiveUPnPStatusRequest(request_object_json: str) -> bool:
    global upnpStatus
    result = friends_receiveGenericFriendRequest(request_object_json, "getUPnPStatus")

    if result is not True:
        return result

    return {"message": "Success", "upnpStatus": upnpStatus}


#####################################################
######## SEND REQUESTS ##############################
#####################################################

def friends_sendGenericRequest(requestKind: str, destAddress: str, connectionMethod: dict = None) -> bool:
    global localSocksPort

    request = friends_craftGenericFriendRequest(destAddress, requestKind)

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    hostname = f"http://{destAddress}/pubEndpoint_receiveGenericFriendRequest"

    if connectionMethod is not None:
        hostname = connectionMethod["hostname"]
        proxies = connectionMethod["proxy"]

    for attempt in range(4):
        try:
            response = requests.post(
                hostname,
                data={'request': request},
                proxies=proxies,
                timeout=15
            )

            try:
                response_json = response.json()
            except json.JSONDecodeError:
                print("Error decoding JSON response.")
                print(response.text)
                response_json = {"error": "Error decoding JSON response."}
            return response.text
        except requests.RequestException as e:
            print(f"Error sending generic request: {e}")
            if attempt < 3:
                print("Retrying in 5 seconds...")
                sleep(5)
            else:
                print("Failed to send generic request after four attempts.")
                return False
    return False


def friends_checkIsMutualFriend(friendAddress: str) -> bool:
    request_response = friends_sendGenericRequest("checkFriend", friendAddress)

    if request_response is False:
        return False

    print(f"[friends_checkIsMutualFriend] Response: {request_response}")

    theyAreMyFriend = friends_isFriend(friendAddress)
    iAmTheirFriend = json.loads(request_response).get("friend")

    if theyAreMyFriend and iAmTheirFriend:
        return True
    else:
        return False


def friends_getFriendIpAddress(friendAddress: str) -> str:
    request_response = friends_sendGenericRequest("getIp", friendAddress)

    parsed_response = json.loads(request_response)

    localIp = parsed_response.get("localIp")
    publicIp = parsed_response.get("publicIp")
    localMiddlewarePort = parsed_response.get("middlewarePort")

    return {"local": localIp, "public": publicIp, "middlewarePort": localMiddlewarePort}   


def friends_checkIsFocusedFriend(friendAddress: str, connectionMethod: dict = None) -> bool:
    request_response = friends_sendGenericRequest("isFocused", friendAddress, connectionMethod)

    if request_response is False:
        return False

    parsed_response = json.loads(request_response)

    if "error" in parsed_response and parsed_response.get("error") == "Origin is not a friend.":
        return False

    return parsed_response.get("isFocused")


def friends_getUPnPStatus(friendAddress: str) -> dict:
    request_response = friends_sendGenericRequest("getUPnPStatus", friendAddress)

    if request_response is False:
        return False

    parsed_response = json.loads(request_response)

    return parsed_response.get("upnpStatus")


#####################################################
######## AUXILIARY FUNCTIONS ########################
#####################################################

def friends_isFriend(address: str) -> bool:
    friends = operator_getFriends()
    for friend in friends:
        if friend["address"] == address:
            return True
    return False


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