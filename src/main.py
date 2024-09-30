import setup
import endpoints

global process
localStorage = {
    "address": "",
    "localSocksPort": 0,
    "localHttpPort": 0,
    "torProcess": None
}

def main():
    global localStorage
    localStorage["torProcess"], localStorage["address"], localStorage["localSocksPort"], localStorage["localHttpPort"] = setup.setupTor()
    endpoints.runServer(localStorage["address"], localStorage["localHttpPort"], localStorage["localSocksPort"])

if __name__ == "__main__":
    main()
