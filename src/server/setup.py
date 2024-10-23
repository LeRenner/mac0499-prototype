import socket
import os
import subprocess
import time

from .p2p import p2p_portIsOpen


def setupTor():
    print("Configurando o tor...")
    process = None
    torAddress = ""
    localSocksPort = 0
    localHttpPort = 0
    torMiddlewarePort = 0

    # find 3 free ports between 5000 and 35000
    for i in range(5876, 35000):
        if p2p_portIsOpen(i):
            localSocksPort = i
            break
    
    if localSocksPort == 5877:
        localSocksPort = 5876
    if localSocksPort == 5880:
        localSocksPort = 5879

    for i in range(localSocksPort + 1, 35000):
        if p2p_portIsOpen(i):
            localHttpPort = i
            break
    
    for i in range(localHttpPort + 1, 35000):
        if p2p_portIsOpen(i):
            torMiddlewarePort = i
            break
    
    # pretty print the ports
    print(f"Usando SOCKS5 na porta {localSocksPort}, HTTP na porta {localHttpPort} e middleware na porta {torMiddlewarePort}.")
    os.sys.stdout.flush()

    # check if ./tor already exists
    if not os.path.exists("./tor"):
        print("Parece que o diretório de configuração do tor ainda não existe. Vamos criá-lo agora.")
        os.sys.stdout.flush()

        # create directories with correct permissions
        os.mkdir("./tor")
        os.mkdir("./tor/data")
        os.mkdir("./tor/data/hidden-service")
        os.mkdir("./logs")
        os.system("chmod -R 700 tor")

    # overwrite torrc file with the correct ports
    torrc = open("./tor/torrc", "w")
    torrc.write("DataDirectory tor/data\nHiddenServiceDir tor/data/hidden-service\nHiddenServicePort 80 127.0.0.1:" + str(torMiddlewarePort) + "\nSocksPort " + str(localSocksPort) + "\nHTTPTunnelPort 0\n")
    torrc.close()

    # create log file
    os.system("touch logs/tor.log")
    log = open("logs/tor.log", "w")
    
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
        torAddress = f.read()
    
    return (process, torAddress, localSocksPort, localHttpPort, torMiddlewarePort)