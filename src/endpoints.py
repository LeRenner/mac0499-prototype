import flask
import logging
import requests

global localHttpPort
global localSocksPort

#############################################################
######## ENDPOINTS ##########################################
#############################################################


def root():
    return "Hello, world!"


def receiveMessage():
    # get the message from the post request
    message = flask.request.form.get("message")
    print(f"Received message: {message}")

    decodedMessage = json.loads(message)
    sender = decodedMessage["sender"]
    content = decodedMessage["content"]

    message = {
        "sender": sender,
        "content": content
    }

    # append message to "messages.txt"
    with open("messages.json", "a") as f:
        f.write(json.dumps(message) + "\n")

    print(f"Message received from {sender}: {content}")

    return "Message received!"


def sendMessage():
    # get message and address from the post request
    message = flask.request.form.get("message")
    decodedMessage = json.loads(message)
    address = decodedMessage["address"]
    content = decodedMessage["content"]

    message = {
        "sender": address,
        "content": content
    }

    message = json.dumps(message)

    print(f"Enviando mensagem para {address}...")
    # send the message to the server

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    response = requests.post(f"http://{address}/receiveMessage", data={"message": message}, proxies=proxies)
    print(response.text)

    print("Mensagem enviada!")

    return "Message sent!"


# generates json and returns request
def getMessages():
    # read all messages from "messages.txt"
    messages = []

    with open("messages.json", "r") as f:
        for line in f:
            messages.append(json.loads(line))

    return json.dumps(messages)


#############################################################
######## INITIALIZE SERVER ##################################
#############################################################

def initializeFlask():
    app = flask.Flask(__name__)

    # Set up logging to a file for Flask
    handler = logging.FileHandler('logs/flask.log')
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    return app


def setupEndpoints(app, address, localSocksPort):
    app.add_url_rule("/", "root", root)
    app.add_url_rule("/receiveMessage", "receiveMessage", receiveMessage, methods=["POST"])
    app.add_url_rule("/sendMessage", "sendMessage", sendMessage, methods=["POST"])
    app.add_url_rule("/getMessages", "getMessages", getMessages)


def runServer(address, argHttpPort, argSocksPort):
    global localHttpPort
    global localSocksPort

    localHttpPort = argHttpPort
    localSocksPort = argSocksPort

    app = initializeFlask()
    setupEndpoints(app, address, localSocksPort)
    app.run(host="localhost", port=localHttpPort)
