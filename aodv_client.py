import threading

import aodvServive
import neighborDiscovery

aodvServ = aodvServive.AODVService()


def requestDiscoveryPath(IP=None):
    return aodvServ.requestDiscoveryPath(toNodeIP=IP)


def sendMessage(recv=None):
    aodvServ.sendMessage(recv=recv)


if __name__ == "__main__":

    t = threading.Thread(target=neighborDiscovery.Revc)
    t.setDaemon(True)
    tt = threading.Thread(target=neighborDiscovery.RecvReply)
    tt.setDaemon(True)

    t.start()
    tt.start()

    aodvServ.start()
