import json
import socket
import subprocess
import threading
import time
from datetime import datetime


def A(routing_table):
    idleTime = {}
    while True:
        if routing_table:
            for route in routing_table:
                toDatetime = datetime.fromtimestamp(route["Lastest_used"])
                diffTime = datetime.now() - toDatetime

                try:
                    idleTime[route["ID"]] = divmod(diffTime.seconds, 60)[0]
                except:
                    idleTime.update({
                        route["ID"]: divmod(diffTime.seconds, 60)[0]
                    })

                if idleTime[route["ID"]] >= route["Lifetime"]:

                    command = "ip -6 route del " + route["nextHop"]
                    subprocess.call(command, shell=True)

                    print("Route ID ", route["ID"], "is expire")
                    routing_table.pop(routing_table.index(route))

                # if checkingTime >= routing_table["Lifetime"]:
                #     print("Expire")
            # print(datetime.now().second - toDatetime.second)

        time.sleep(10)
    # while True:
    #     if routing_table:
    #         divv = datetime.fromtimestamp(routing_table["Lastest_used"])
    #         print(divv.second - routing_table["Lifetime"] *60)
    #         time.sleep(5)


class UDPSocketServer(threading.Thread):
    bufferSize = 2048

    def __init__(self, listNode, nodeName):

        super().__init__()
        self.listNode = listNode
        self.node = self.listNode[nodeName]
        self.rreq_data_packet = None
        self.rrep_data_packet = None
        self.trickFirstRouting = False

    def getNode(self):
        return

    def runExpireTimer(self):
        print("################## Timer at " + self.node["Name"] + " Start ###############")
        self.trickFirstRouting = True
        t = threading.Thread(target=A, args=(self.node["ROUTING_TABLE"],))
        t.setDaemon(True)
        t.start()

    def run(self):

        ## Start UDP Server
        udpServer = socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM)
        udpServer.bind(("::", self.node["Port"]))

        ## Call to Expiretimer tread
        self.runExpireTimer()

        while True:

            # Receive the data from udp socket
            revMessage = udpServer.recvfrom(UDPSocketServer.bufferSize)[0]

            # If have message
            if revMessage:

                # Conevert message to dictionary
                revMessage = revMessage.decode()
                revMessage = json.loads(revMessage)

                if revMessage["mode"] == 0:

                    # Is RREQ and not source node
                    if revMessage["data"]["isRREQ"] and revMessage["data"]["sourceAddr"] != self.node["IP"]:
                        self.aodvRREQ(revMessage["data"])

                    # Is RREP and not source node ( Destination from source )
                    elif not revMessage["data"]["isRREQ"] and revMessage["data"]["sourceAddr"] != self.node["IP"]:
                        self.aodvRREP(revMessage["data"])

                    # RREQ
                    if self.rrep_data_packet is None and revMessage["data"]["sourceAddr"] != self.node["IP"]:

                        # From source boardcast to neighbor
                        if self.node["IP"] != self.rreq_data_packet["destAddr"] and self.node["IP"] != \
                                self.rreq_data_packet["sourceAddr"]:
                            # print(self.node["Name"])
                            for neighbor in self.node["neighbors"]:
                                if neighbor != self.rreq_data_packet["sourceAddr"]:
                                    # print(neighbor)
                                    self.__sendRequest(neighborIP=neighbor, isRREQ=True)

                        # At Destination node is end of RREQ packet and set to RREP packet then sent back from next hop
                        # of RREQ message
                        elif self.node["IP"] == self.rreq_data_packet["destAddr"]:
                            self.rrep_data_packet = {
                                "sourceAddr": self.rreq_data_packet["destAddr"],
                                "destAddr": self.rreq_data_packet["sourceAddr"],
                                "destSeq": 120,
                                "hopCount": 0,
                                "sentFrom": self.node["IP"],
                                "isRREQ": False,
                                "Lifetime": 1  # if 0 is not expire || unit is min
                            }

                            self.__sendRequest(neighborIP=self.node["RREQ_MESSAGE"][-1]["nextHop"], isRREQ=False)

                    # RREP
                    elif self.rrep_data_packet is not None and revMessage["data"]["sourceAddr"] != self.node["IP"]:

                        # RREP packet then sent back from next hop of RREQ message
                        if self.node["IP"] != self.rrep_data_packet["destAddr"] and self.node["IP"] != \
                                self.rrep_data_packet["sourceAddr"]:
                            # print(self.node["Name"])
                            self.__sendRequest(neighborIP=self.node["RREQ_MESSAGE"][-1]["nextHop"], isRREQ=False)

                        # If this node is RREP destination
                        else:
                            self.rreq_data_packet = None
                            self.rrep_data_packet = None

                    # If from requestDiscoveryPath
                    else:
                        self.rreq_data_packet = revMessage["data"]

                        for neighbor in self.node["neighbors"]:
                            if neighbor != self.rreq_data_packet["sourceAddr"]:
                                # print(neighbor)
                                self.__sendRequest(neighborIP=neighbor, isRREQ=True)

                elif revMessage["mode"] == 1:

                    print("listNode.json is update!")
                    self.listNode = revMessage["data"]
                    self.writeToListNodeJson()

                    print(json.dumps(self.listNode, indent=2))

    def __sendRequest(self, neighborIP=None, isRREQ=True):

        # Get socket address
        sockAddr = socket.getaddrinfo(self.listNode[neighborIP]["IP"], self.listNode[neighborIP]["Port"],
                                      family=socket.AF_INET6, proto=socket.IPPROTO_UDP)

        with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:
            toNodeMsg = {
                "mode": 0,
                "data": self.rreq_data_packet if isRREQ else self.rrep_data_packet
            }

            ss.sendto(json.dumps(toNodeMsg).encode(), sockAddr[0][4])
            ss.close()

    def requestDiscoveryPath(self, toNodeIP=None):
        sockAddr = socket.getaddrinfo(self.node["IP"], self.node["Port"], family=socket.AF_INET6,
                                      proto=socket.IPPROTO_UDP)

        with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as ss:
            rreq_data_packet = {
                "sourceAddr": self.node["IP"],
                "seqSource": 1,
                "RreqId": self.node["ID"],
                "destAddr": toNodeIP,
                "destSeq": None,
                "hopCount": 0,
                "sentFrom": self.node["IP"],
                "isRREQ": True,
                "RequestTime": {}
            }
            rreq_data_packet["RequestTime"].update({
                self.node["IP"]: datetime.timestamp(datetime.now())
            })

            toNodeMsg = {
                "mode": 0,
                "data": rreq_data_packet
            }

            ss.sendto(json.dumps(toNodeMsg).encode(), sockAddr[0][4])
            ss.close()

    def getRoutingTable(self):
        for reccord in self.node["ROUTING_TABLE"]:
            print("Routing table of node " + self.node["IP"])
            print(reccord, end="\n\n")

    def aodvRREQ(self, revMessage):

        self.rreq_data_packet = revMessage
        self.rreq_data_packet["hopCount"] += 1
        self.rreq_data_packet["RequestTime"].update({
            self.node["IP"]: datetime.timestamp(datetime.now())
        })

        rreq_message = {
            "destAddr": self.rreq_data_packet["sourceAddr"],
            "nextHop": self.rreq_data_packet["sentFrom"],
            "hopCount": self.rreq_data_packet["hopCount"],
            "seq": self.rreq_data_packet["seqSource"]
        }
        self.node["RREQ_MESSAGE"].append(rreq_message)
        self.rreq_data_packet["sentFrom"] = self.node["IP"]

    def aodvRREP(self, revMessage):

        self.rrep_data_packet = revMessage
        self.rrep_data_packet["hopCount"] += 1

        rrep_message = {
            "ID": len(self.node["ROUTING_TABLE"]) + 1,
            "destAddr": self.rrep_data_packet["sourceAddr"],
            "nextHop": self.rrep_data_packet["sentFrom"],
            "hopCount": self.rrep_data_packet["hopCount"],
            "seq": self.rrep_data_packet["destSeq"]
        }

        RREP_Time = datetime.now()
        duration = RREP_Time - datetime.fromtimestamp(
            self.rreq_data_packet["RequestTime"][self.node["IP"]]
        )
        Latency_Time = duration.microseconds * (10 ** -3)
        rrep_message.update({
            "LatencyTime": str(Latency_Time) + " ms",
            "Lifetime": self.rrep_data_packet["Lifetime"],
            "Lastest_used": datetime.timestamp(datetime.now())
        })

        self.node["ROUTING_TABLE"].append(rrep_message)

        command = "ip -6 route add "+ rrep_message["destAddr"] +" dev wlan0 via "+ rrep_message["nextHop"]
        subprocess.call(command, shell=True)

        self.rrep_data_packet["sentFrom"] = self.node["IP"]

    def writeToListNodeJson(self):
        with open('listNode.json', 'w') as outfile:
            json.dump(self.listNode, outfile, indent=2)
