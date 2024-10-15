import flask
import requests
import socket
import logging

from .privateEndpoints import *
from .publicEndpoints import *
from .serverCrypto import crypto_initializeTorKeys
from .jsonOperator import operator_setupVariables
from .p2p import p2p_initializeVariables
from .friends import friends_initializeVariables


#############################################################
######## INITIALIZE SERVER ##################################
#############################################################

def endpoints_initializeFlask():
    app = flask.Flask(__name__)

    # Set up logging to a file for Flask
    handler = logging.FileHandler('logs/flask.log')
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    return app


def endpoints_setupEndpoints(app, address, localSocksPort):
    privEndpoint_setupPrivateEndpointVariables(address, localSocksPort)
    pubEndpoint_setupPublicEndpointlVariables(localSocksPort)
    p2p_initializeVariables(localSocksPort)
    friends_initializeVariables(localSocksPort)
    operator_setupVariables(address)
    crypto_initializeTorKeys()

    publicEndpoints = [
        ["pubEndpoint_receiveMessage", "POST"],
        ["pubEndpoint_getPublicKeyBase64", "GET"],
        ["pubEndpoint_checkFriendRequest", "POST"],
        ["pubEndpoint_getIpRequest", "POST"],
        ["pubEndpoint_getFriendIP", "POST"],
        ["pubEndpoint_p2pRequest", "GET"],
    ]
    
    privateEndpoints = [
        ["privEndpoint_getMessagesFromSender", "POST"],
        ["privEndpoint_sendMessage", "POST"],
        ["privEndpoint_getLatestMessages", "GET"],
        ["privEndpoint_getSenders", "GET"],
        ["privEndpoint_getAddress", "GET"],
        ["privEndpoint_startChat", "POST"],
        ["privEndpoint_getFriends", "GET"],
        ["privEndpoint_addFriend", "POST"],
        ["privEndpoint_removeFriend", "POST"],
        ["privEndpoint_changeFocusedFriend", "POST"],
        ["privEndpoint_getFriendConectionStatus", "GET"]
    ]
    
    def check_tor_middleware_header():
        endpoint = flask.request.url.split("/")[-1]
        endpointInPublicEndpoints = False

        for publicEndpoint in publicEndpoints:
            if publicEndpoint[0] == endpoint:
                endpointInPublicEndpoints = True
                break

        hasTorExternalHeader = flask.request.headers.get('Tor-Middleware-Header') == 'True'

        if not endpointInPublicEndpoints and hasTorExternalHeader:
            flask.abort(403)

    # Public endpoints
    for endpoint, method in publicEndpoints:
        app.add_url_rule(f"/{endpoint}", endpoint, globals().get(endpoint), methods=[method])

    # Private endpoints with middleware check
    app.before_request(check_tor_middleware_header)
    for endpoint, method in privateEndpoints:
        app.add_url_rule(f"/{endpoint}", endpoint, globals().get(endpoint), methods=[method])

    app.add_url_rule("/web", "privEndpoint_webInterface", privEndpoint_webInterface, defaults={'filename': ''}, methods=["GET"])
    app.add_url_rule("/web/", "privEndpoint_webInterface", privEndpoint_webInterface, defaults={'filename': ''}, methods=["GET"])
    app.add_url_rule("/web/<path:filename>", "privEndpoint_webInterface", privEndpoint_webInterface, methods=["GET"])


def endpoints_runServer(argAddress, argHttpPort, argSocksPort):
    global localHttpPort
    global localSocksPort
    global address

    localHttpPort = argHttpPort
    localSocksPort = argSocksPort
    address = argAddress

    app = endpoints_initializeFlask()
    endpoints_setupEndpoints(app, address, localSocksPort)
    app.run(host="localhost", port=localHttpPort)
