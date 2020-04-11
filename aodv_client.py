import aodvServive

aodvServ = aodvServive.AODVService()

def requestDiscoveryPath(IP=None):
    return aodvServ.requestDiscoveryPath(toNodeIP=IP)

if __name__ == "__main__":
    aodvServ.start()
