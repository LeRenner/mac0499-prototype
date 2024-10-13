from .serverCrypto import *

def craftCheckFriendRequest(destAddress: str) -> str:
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
    signature = signMessage(request_json)

    # Create the final request object
    request_object = {
        "request": request,
        "signature": signature,
        "pubKey": publicKeyInBase64()
    }

    # Serialize the request object as JSON
    request_object_json = json.dumps(request_object)

    return request_object_json


def processCheckFriendRequest(request_object_json: str) -> bool:
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
    if not verifyMessage(request, signature, base64.b64decode(pubKey)):
        return {"message": "Invalid signature."}
    
    # Check if the address and public key match
    if origin != generateTorAddressFromBase64(pubKey):
        return {"message": "Invalid public key."}
    
    if kind != "checkFriend":
        return {"message": "Invalid kind."}
    
    # Check if the timestamp is within the last 2 minutes
    if int(datetime.datetime.now().timestamp()) - timestamp > 120:
        return {"message": "Request is too old."}
    
    # Check if the destination address matches the local address
    if destination != getOwnAddress():
        return {"message": "Destination address does not match."}
    
    # Check if the origin address is already a friend
    try:
        with open("storage.json", "r") as f:
            storage = json.load(f)
    except FileNotFoundError:
        storage = {"friends": []}

    friends = storage.get("friends", [])
    if any(f["address"] == origin for f in friends):
        saveFriendPubKey(pubKey)
        return {"message": "Success", "friend": 1}
    
    return {"message": "Success", "friend": 0}


# def craftGetFriendIPRequest(destAddress: str) -> str:


def getFriendIPHandler(request_object_json: str) -> str:
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
    if not verifyMessage(request, signature, base64.b64decode(pubKey)):
        return json.dumps({"error": "Invalid signature."})
    
    # Check if the address and public key match
    if origin != generateTorAddressFromBase64(pubKey):
        return json.dumps({"error": "Invalid public key."})
    
    # Check if the timestamp is within the last 2 minutes
    if int(datetime.datetime.now().timestamp()) - timestamp > 120:
        return json.dumps({"error": "Request is too old."})
    
    # Check if the destination address matches the local address
    if destination != getOwnAddress():
        return json.dumps({"error": "Destination address does not match."})
    
    # Check request kind
    if kind != "getFriendIP":
        return json.dumps({"error": "Invalid kind."})
    
    # Get the friend's public key
    try:
        response = requests.post(f"http://localhost:{localHttpPort}/getPublicKey", data={"request": request_object_json})
        friendPublicKey = response.json()["publicKey"]
    except requests.exceptions.RequestException:
        return json.dumps({"error": "Failed to fetch friend's public key."})
    
    # Calculate the friend's IP address
    friendIP = torAddressFromBase64(friendPublicKey)

    return json.dumps({"friendIP": friendIP})


#########################################################################
############ Auxiliary functions ########################################
#########################################################################
