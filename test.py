import json
import time
import scserver

listNode = {}

nodeC = {
    "ID": 3,
    "Name": "nodeC",
    "IP": "127.0.0.1",
    "Port": 1236,
    "neighbors": ["nodeB"],
    "RREQ_MESSAGE": [],
    "ROUTING_TABLE": [],
}

nodeB = {
    "ID": 2,
    "Name": "nodeB",
    "IP": "127.0.0.1",
    "Port": 1235,
    "neighbors": ["nodeA", "nodeC"],
    "RREQ_MESSAGE": [],
    "ROUTING_TABLE": []
}

nodeA = {
    "ID": 1,
    "Name": "nodeA",
    "IP": "127.0.0.1",
    "Port": 1234,
    "neighbors": ["nodeB"],
    "RREQ_MESSAGE": [],
    "ROUTING_TABLE": []
}

listNode.update({
    "nodeA": nodeA,
    "nodeB": nodeB,
    "nodeC": nodeC
})

udpServer = scserver.UDPSocketServer(listNode, 'nodeA')
udpServer1 = scserver.UDPSocketServer(listNode, 'nodeB')
udpServer2 = scserver.UDPSocketServer(listNode, 'nodeC')

if __name__ == "__main__":
    udpServer.start()
    udpServer1.start()
    udpServer2.start()

    udpServer.requestDiscoveryPath(toNode="nodeC")
    udpServer2.requestDiscoveryPath(toNode="nodeA")
    time.sleep(0.5)
    udpServer.getRoutingTable()
    udpServer1.getRoutingTable()
    udpServer2.getRoutingTable()

    print("\n\n\n\n")
    time.sleep(62)
    udpServer.getRoutingTable()
    udpServer1.getRoutingTable()
    udpServer2.getRoutingTable()

    # print(json.dumps(listNode, indent=2))
