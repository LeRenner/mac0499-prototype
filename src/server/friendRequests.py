from .serverCrypto import *
from .jsonOperator import *

def craftpubEndpoint_checkFriendRequest(destAddress: str) -> str:
    global address

    request = {
        "origin": address,
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
        "signature": signature,
        "pubKey": publicKeyInBase64()
    }

    # Serialize the request object as JSON
    request_object_json = json.dumps(request_object)

    return request_object_json


def processpubEndpoint_checkFriendRequest(request_object_json: str) -> bool:
    # Deserialize the request object
    request_object = json.loads(request_object_json)

    # Extract the request and signature
    request = request_object["request"]
    signature = request_object["signature"]
    pubKey = request_object["pubKey"]

    requestObj = json.loads(request)

    origin = requestObj["origin"]
    destination = requestObj["destination"]
    timestamp = requestObj["timestamp"]
    kind = requestObj["kind"]

    # Verify the signature
    if not crypto_verifyMessage(request, signature, base64.b64decode(pubKey)):
        return {"message": "Invalid signature."}
    
    # Check if the address and public key match
    if origin != crypto_generateTorAddressFromBase64(pubKey):
        return {"message": "Invalid public key."}
    
    if kind != "checkFriend":
        return {"message": "Invalid kind."}
    
    # Check if the timestamp is within the last 2 minutes
    if int(datetime.datetime.now().timestamp()) - timestamp > 120:
        return {"message": "Request is too old."}
    
    # Check if the destination address matches the local address
    if destination != crypto_getOwnAddress():
        return {"message": "Destination address does not match."}
    
    friends = operator_getFriends()
    if origin in friends:
        saveFriendPubKey(pubKey)
        return {"message": "Success", "friend": 1}
    
    return {"message": "Success", "friend": 0}


# def craftpubEndpoint_getFriendIPRequest(destAddress: str) -> str:


def pubEndpoint_getFriendIPHandler(request_object_json: str) -> str:
    # Deserialize the request object
    request_object = json.loads(request_object_json)

    # Extract the request and signature
    request = request_object["request"]
    signature = request_object["signature"]
    pubKey = request_object["pubKey"]

    requestObj = json.loads(request)

    origin = requestObj["origin"]
    destination = requestObj["destination"]
    timestamp = requestObj["timestamp"]
    kind = requestObj["kind"]

    # Verify the signature
    if not crypto_verifyMessage(request, signature, base64.b64decode(pubKey)):
        return json.dumps({"error": "Invalid signature."})
    
    # Check if the address and public key match
    if origin != crypto_generateTorAddressFromBase64(pubKey):
        return json.dumps({"error": "Invalid public key."})
    
    # Check if the timestamp is within the last 2 minutes
    if int(datetime.datetime.now().timestamp()) - timestamp > 120:
        return json.dumps({"error": "Request is too old."})
    
    # Check if the destination address matches the local address
    if destination != crypto_getOwnAddress():
        return json.dumps({"error": "Destination address does not match."})
    
    # Check request kind
    if kind != "pubEndpoint_getFriendIP":
        return json.dumps({"error": "Invalid kind."})
    
    # Calculate the friend's IP address
    friendIP = torAddressFromBase64(friendPublicKey)

    return json.dumps({"friendIP": friendIP})


#########################################################################
############ Auxiliary functions ########################################
#########################################################################
