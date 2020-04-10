import aodvServive

aodvServ = aodvServive.AODVService()

def requestDiscoveryPath(IP=None):
    print("to ip " + IP)
    aodvServ.requestDiscoveryPath(toNodeIP=IP)

if __name__ == "__main__":
    aodvServ.start()
