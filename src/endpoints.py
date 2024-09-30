import flask
import logging
import requests
import json

global localHttpPort
global localSocksPort
global address

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
    with open("messages.txt", "a") as f:
        f.write(json.dumps(message) + "\n")

    print(f"Message received from {sender}: {content}")

    return "Message received!"


def sendMessage():
    global localSocksPort
    global address

    # get message and address from the post request
    decodedMessage = json.loads(flask.request.form.get("message"))
    destination = decodedMessage["address"]
    messageContent = decodedMessage["message"]

    print(f"Enviando mensagem para {destination}...")
    print(f"Conteúdo: {messageContent}")

    message = {
        "sender": address,
        "content": messageContent
    }

    packagedMessage = json.dumps(message)

    print(f"Enviando mensagem para {destination}...")
    # send the message to the server

    proxies = {
        'http': 'socks5h://localhost:{}'.format(localSocksPort)
    }

    response = requests.post(f"http://{destination}/receiveMessage", data={"message": packagedMessage}, proxies=proxies)
    print(response.text)

    print("Mensagem enviada!")

    return "Message sent!"


# generates json and returns request
def getMessages():
    # read all messages from "messages.txt"
    messages = []

    messageFile = open("messages.txt", "r")
    messageList = messageFile.readlines()
    messageFile.close()

    print(messageList)

    for line in messageList:
        print(f"Reading line: {line}")
        if line.strip() == "" or line.strip() == "\n":
            continue
        else:
            try:
                message = json.loads(line)
                messages.append(message)
            except json.JSONDecodeError:
                print(f"Error decoding message: {line}")

    print(f"Returning messages: {messages}")

    response = {
        "messages": messages
    }

    return json.dumps(response)


def webInterface(filename):
    if filename == "":
        filename = "index.html"

    return flask.send_from_directory("web", filename)


#############################################################
######## INITIALIZE SERVER ##################################
#############################################################

def initializeFlask():
    app = flask.Flask(__name__)

    # Set up logging to a file for Flask
    handler = logging.FileHandler('logs/flask.log')
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    # create messages.txt file
    with open("messages.txt", "a") as f:
        pass

    return app


def setupEndpoints(app, address, localSocksPort):
    app.add_url_rule("/", "root", root)
    app.add_url_rule("/receiveMessage", "receiveMessage", receiveMessage, methods=["POST"])
    app.add_url_rule("/sendMessage", "sendMessage", sendMessage, methods=["POST"])
    app.add_url_rule("/getMessages", "getMessages", getMessages)
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
