import flask
import requests
import socket
import logging

from .privateEndpoints import *
from .publicEndpoints import *


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

    def check_tor_middleware_header():
        if flask.request.endpoint != 'receiveMessage' and flask.request.headers.get('Tor-Middleware-Header') == 'True':
            flask.abort(403)

    # Public endpoints
    app.add_url_rule("/receiveMessage", "receiveMessage", receiveMessage, methods=["POST"])

    # Private endpoints with middleware check
    app.before_request(check_tor_middleware_header)
    app.add_url_rule("/", "root", root)
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