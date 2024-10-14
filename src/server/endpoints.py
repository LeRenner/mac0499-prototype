import flask
import requests
import socket
import logging

from .privateEndpoints import *
from .publicEndpoints import *
from .serverCrypto import *


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
    setupPrivateEndpointVariables(address, localSocksPort)
    initializeTorKeys()

    publicEndpoints = [
        ["receiveMessage", "POST"]
    ]
    
    privateEndpoints = [
        ["getMessagesFromSender", "POST"],
        ["sendMessage", "POST"],
        ["getLatestMessages", "GET"],
        ["getSenders", "GET"],
        ["getAddress", "GET"],
        ["startChat", "POST"],
        ["getFriends", "GET"],
        ["addFriend", "POST"],
        ["removeFriend", "POST"],
        ["isVerifiedSender", "POST"]
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
        app.add_url_rule(f"/{endpoint}", endpoint, globals()[endpoint], methods=[method])

    # Private endpoints with middleware check
    app.before_request(check_tor_middleware_header)
    for endpoint, method in privateEndpoints:
        app.add_url_rule(f"/{endpoint}", endpoint, globals()[endpoint], methods=[method])

    app.add_url_rule("/web", "webInterface", webInterface, defaults={'filename': ''}, methods=["GET"])
    app.add_url_rule("/web/", "webInterface", webInterface, defaults={'filename': ''}, methods=["GET"])
    app.add_url_rule("/web/<path:filename>", "webInterface", webInterface, methods=["GET"])


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


#############################################################
######## AUXILIARY FUNCTIONS ################################
#############################################################

def getPublicIP():
    try:
        response = requests.get("http://httpbin.org/ip")
        return response.json()["origin"]
    except requests.exceptions.RequestException:
        return None


def getLocalIP():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip