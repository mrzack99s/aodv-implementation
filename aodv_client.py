import aodvServive

aodvServ = aodvServive.AODVService()


def requestDiscoveryPath(IP=None):
    return aodvServ.requestDiscoveryPath(toNodeIP=IP)


def sendMessage(recv=None):
    aodvServ.sendMessage(recv=recv)


if __name__ == "__main__":
    aodvServ.start()
