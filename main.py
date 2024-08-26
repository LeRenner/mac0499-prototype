import os
import subprocess
import time
import flask
import signal
import sys
import logging
import threading
import json
import requests

global process
global localStorage
localStorage = {
    "address": "",
    "localSocksPort": 0,
    "localHttpPort": 0,
    "messages": []
}

def setupTor():
    global process
    global localStorage

    # find 2 free ports between 5000 and 35000
    for i in range(5000, 35000):
        if not os.system(f"lsof -i:{i}"):
            localStorage["localSocksPort"] = i
            break

    for i in range(5000, 35000):
        if not os.system(f"lsof -i:{i}"):
            localStorage["localHttpPort"] = i
            break
    
    # pretty print the ports
    print(f"Usando SOCKS5 na porta {localStorage['localSocksPort']} e HTTP na porta {localStorage['localHttpPort']}")

    # check if ./tor already exists
    if not os.path.exists("./tor"):
        print("Parece que o diretório de configuração do tor ainda não existe. Vamos criá-lo agora.")
        os.sys.stdout.flush()

        # create directories with correct permissions
        os.mkdir("./tor")
        os.mkdir("./tor/data")
        os.mkdir("./tor/data/hidden-service")
        os.system("chmod -R 700 tor")

        torrc = open("./tor/torrc", "w")
        torrc.write("DataDirectory tor/data\nHiddenServiceDir tor/data/hidden-service\nHiddenServicePort 80 127.0.0.1:9666\nSocksPort 9665\nHTTPTunnelPort 0\n")
        torrc.close()

    # create log file
    log = open("log.txt", "a")
    
    # start tor
    process = subprocess.Popen(["tor", "-f", "tor/torrc"], stdout=log, stderr=log)

    # wait for the creation of tor/data/hidden-service/hostname
    print("Esperando o tor iniciar.", end="")
    os.sys.stdout.flush()

    while not os.path.exists("./tor/data/hidden-service/hostname"):
        time.sleep(1)
        print(".", end="")
        os.sys.stdout.flush()
    print()

    print("Seu endereço .onion é:\n")
    with open("./tor/data/hidden-service/hostname") as f:
        print(f.read())
    os.sys.stdout.flush()

    # store the address in the global variable
    with open("./tor/data/hidden-service/hostname") as f:
        localStorage["address"] = f.read()

def runServer():
    app = flask.Flask(__name__)

    # Suppress the Flask server startup messages
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Set up logging to a file for Flask
    handler = logging.FileHandler('flask.log')
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    @app.route("/")
    def index():
        return "Hello, World!"

    # receive post on /receiveMessage
    @app.route("/receiveMessage", methods=["POST"])
    def receiveMessage():
        global localStorage

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

        # store the message in the global variable
        localStorage["messages"].append(message)

        print(f"Message received from {sender}: {content}")

        return "Message received!"

    # Run the Flask server
    app.run(host="localhost", port=9666)

def signal_handler(sig, frame):
    print("\nRecebido SIGINT, terminando processo...")
    if process:
        process.terminate()
        process.wait()  # Wait for the process to terminate
    sys.exit(0)

def sendMessage():
    global localStorage

    address = input("Digite o endereço tor do destinatário: ")
    content = input("Digite a mensagem que deseja enviar: ")

    # send POST request using SOCKS5 localhost:9665 to /receiveMessage
    # send the message in the form of a json string
    
    message = {
        "sender": localStorage["address"],
        "content": content
    }

    message = json.dumps(message)

    print(f"Enviando mensagem para {address}...")

    # send the message to the server
    proxies = {
        'http': 'socks5h://localhost:9665'
    }
    response = requests.post(f"http://{address}/receiveMessage", data={"message": message}, proxies=proxies)
    print(response.text)

    print("Mensagem enviada!")

# endless function that 
def userInterface():
    # Ask user if they want to send a message
    while True:
        user_input = input("Deseja enviar uma mensagem? (s/n) ")
        if user_input.lower() == "n":
            continue
        elif user_input.lower() == "s":
            sendMessage()
        else:
            print("Entrada inválida. Tente novamente.")
            continue


def main():
    signal.signal(signal.SIGINT, signal_handler)
    setupTor()

    # Run Flask server in a separate thread
    server_thread = threading.Thread(target=runServer)
    server_thread.daemon = True  # This ensures the thread will exit when the main program exits
    server_thread.start()

    # Run the user interface
    userInterface()


if __name__ == "__main__":
    main()
