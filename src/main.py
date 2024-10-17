import server.setup
import server.endpoints
import server.middleware

import threading

global process
localStorage = {
    "address": "",
    "localSocksPort": 0,
    "localHttpPort": 0,
    "torMiddlewarePort": 0,
    "torProcess": None
}

def main():
    global localStorage
    localStorage["torProcess"], localStorage["address"], localStorage["localSocksPort"], localStorage["localHttpPort"], localStorage["torMiddlewarePort"] = server.setup.setupTor()
    
    # run the middleware server
    server_thread = threading.Thread(target=server.middleware.runMiddleware, args=(localStorage["torMiddlewarePort"], localStorage["localHttpPort"]))
    server_thread.start()

    # run the main server
    server.endpoints.endpoints_runServer(localStorage["address"], localStorage["localHttpPort"], localStorage["localSocksPort"], localStorage["torMiddlewarePort"])

if __name__ == "__main__":
    main()
