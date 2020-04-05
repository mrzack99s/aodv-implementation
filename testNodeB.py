import json
import socket
import subprocess
import time
import scserver

def getListNodeFromJson():
    with open('listNode.json') as json_file:
        return json.load(json_file)


listNode = getListNodeFromJson()
hostname = socket.gethostname()
ownIPv6 = socket.getaddrinfo(hostname, None, socket.AF_INET6,socket.SOCK_DGRAM)[0][4][0]
udpServer = scserver.UDPSocketServer(listNode, ownIPv6)

# Flush neighbor
subprocess.call("ip -6 neigh flush dev wlan0", shell=True)
subprocess.call("ip neigh flush dev wlan0", shell=True)

#Assign neighbor
for neighbor in listNode[ownIPv6]["neighbors"]:
    command = "ip -6 neighbor add "+ listNode[neighbor]["IP"] +" lladdr "+ listNode[neighbor]["intMacAddr"] +" dev wlan0 nud reachable "
    subprocess.call(command, shell=True)

if __name__ == "__main__":
    udpServer.start()
    #udpServer.requestDiscoveryPath(toNode="nodeB")
    #udpServer2.requestDiscoveryPath(toNode="nodeA")
    #time.sleep(30)
    #udpServer.getRoutingTable()
    time.sleep(65)
    print("\nRouting checking")
    udpServer.getRoutingTable()

    # print("\n\n\n\n")
    # time.sleep(62)
    # udpServer.getRoutingTable()
    # udpServer1.getRoutingTable()
    # udpServer2.getRoutingTable()

    # print(json.dumps(listNode, indent=2))
