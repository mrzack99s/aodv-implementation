import json
import time
import scserver

listNode = {}

nodeC = {
    "ID": 3,
    "Name": "nodeC",
    "IP": "::1",
    "Port": 20003,
    "neighbors": ["nodeB"],
    "RREQ_MESSAGE": [],
    "ROUTING_TABLE": [],
}

nodeB = {
    "ID": 2,
    "Name": "nodeB",
    "IP": "fe80::ba27:ebff:fe59:aa80",
    "Port": 20002,
    "neighbors": ["nodeA", "nodeC"],
    "RREQ_MESSAGE": [],
    "ROUTING_TABLE": []
}

nodeA = {
    "ID": 1,
    "Name": "nodeA",
    "IP": "fe80::ba27:ebff:feaa:40aa",
    "Port": 20001,
    "neighbors": ["nodeB"],
    "RREQ_MESSAGE": [],
    "ROUTING_TABLE": []
}

listNode.update({
    "nodeA": nodeA,
    "nodeB": nodeB,
    "nodeC": nodeC
})

udpServer = scserver.UDPSocketServer(listNode, 'nodeB')

if __name__ == "__main__":
    udpServer.start()
    #udpServer.requestDiscoveryPath(toNode="nodeB")
    #udpServer2.requestDiscoveryPath(toNode="nodeA")
    #time.sleep(30)
    #udpServer.getRoutingTable()

    # print("\n\n\n\n")
    # time.sleep(62)
    # udpServer.getRoutingTable()
    # udpServer1.getRoutingTable()
    # udpServer2.getRoutingTable()

    # print(json.dumps(listNode, indent=2))
