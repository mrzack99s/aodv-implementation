from datetime import datetime
import json
import socket
import time

import scserver

listNode = {}
Rreq_time = None
Rrep_time = None

nodeC = {
            "ID":3,
            "Name": "nodeC",
            "IP": "127.0.0.1",
            "Port":1236,
            "neighbors": ["nodeB"],
            "rev": []
        }

nodeB = {
            "ID":2,
            "Name": "nodeB",
            "IP": "127.0.0.1",
            "Port": 1235,
            "neighbors": ["nodeA", "nodeC"],
            "rev": []
        }

nodeA = {
            "ID": 1,
            "Name": "nodeA",
            "IP": "127.0.0.1",
            "Port": 1234,
            "neighbors": ["nodeB"],
            "rev": []
        }

listNode.update({
            "nodeA": nodeA,
            "nodeB": nodeB,
            "nodeC": nodeC
        })

udpServer = scserver.UDPSocketServer(listNode,'nodeA')
udpServer1 = scserver.UDPSocketServer(listNode,'nodeB')
udpServer2 = scserver.UDPSocketServer(listNode,'nodeC')

def sendRequest(Source=None,Dest=None,From=None):
    Rrep_time = datetime.now()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for neighbor in listNode[From]["neighbors"]:
        if neighbor != From:
            print("Call node "+neighbor)
            s.connect((listNode[neighbor]["IP"], listNode[neighbor]["Port"]))

    rreq_data_packet = {
        "sourceAddr": Source,
        "seqSource": 1,
        "RreqId": listNode[Dest]["ID"],
        "destAddr": Dest,
        "destSeq": None,
        "hopCount": 0,
        "sentFrom": From,
        "isRREQ": True
    }
    s.send(json.dumps(rreq_data_packet).encode())
    s.close()

if __name__ == "__main__":
    udpServer.start()
    udpServer1.start()
    udpServer2.start()
    sendRequest(Source="nodeA",Dest="nodeC",From="nodeA")
    time.sleep(0.5)
    print(listNode)

